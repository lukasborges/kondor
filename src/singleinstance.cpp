#include "singleinstance.h"

#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLocalSocket>

#ifdef Q_OS_UNIX
#include <unistd.h>
#endif

namespace {
// A command line is tiny; anything bigger than this is not one of ours.
constexpr int kMaxMessageSize = 1024 * 1024;
}

SingleInstance::SingleInstance(const QString &serverName, QObject *parent)
    : QObject(parent)
    , m_name(serverName.isEmpty() ? SingleInstance::serverName() : serverName)
{
    connect(&m_server, &QLocalServer::newConnection,
            this, &SingleInstance::handleNewConnection);
}

SingleInstance::~SingleInstance() = default;

QString SingleInstance::serverName()
{
#ifdef Q_OS_UNIX
    return QStringLiteral("kondor-") + QString::number(getuid());
#else
    return QStringLiteral("kondor-") + qEnvironmentVariable("USER");
#endif
}

QByteArray SingleInstance::encodeMessage(const SingleInstanceMessage &message)
{
    QJsonArray urls;
    for (const QUrl &url : message.urls)
        urls.append(QString::fromUtf8(url.toEncoded()));

    QJsonObject object;
    object.insert(QStringLiteral("urls"), urls);
    object.insert(QStringLiteral("private"), message.privateMode);
    object.insert(QStringLiteral("newWindow"), message.newWindow);
    object.insert(QStringLiteral("activationToken"),
                  QString::fromUtf8(message.activationToken));

    return QJsonDocument(object).toJson(QJsonDocument::Compact) + '\n';
}

SingleInstanceMessage SingleInstance::decodeMessage(const QByteArray &line)
{
    SingleInstanceMessage message;
    const QJsonDocument document = QJsonDocument::fromJson(line.trimmed());
    if (!document.isObject())
        return message;

    const QJsonObject object = document.object();
    const QJsonArray urls = object.value(QStringLiteral("urls")).toArray();
    for (const QJsonValue &value : urls) {
        const QUrl url = QUrl::fromEncoded(value.toString().toUtf8());
        if (url.isValid() && !url.isEmpty())
            message.urls.append(url);
    }
    message.privateMode = object.value(QStringLiteral("private")).toBool();
    message.newWindow = object.value(QStringLiteral("newWindow")).toBool();
    message.activationToken =
        object.value(QStringLiteral("activationToken")).toString().toUtf8();
    return message;
}

bool SingleInstance::sendMessage(const SingleInstanceMessage &message)
{
    QLocalSocket socket;
    socket.connectToServer(m_name);
    if (!socket.waitForConnected(500))
        return false;

    socket.write(encodeMessage(message));
    // write() usually flushes everything at once for a local socket; only wait
    // when some bytes are still buffered.
    if (socket.bytesToWrite() > 0 && !socket.waitForBytesWritten(500))
        return false;
    socket.disconnectFromServer();
    if (socket.state() != QLocalSocket::UnconnectedState)
        socket.waitForDisconnected(500);
    return true;
}

SingleInstance::StartResult SingleInstance::start(const SingleInstanceMessage &message)
{
    if (m_server.listen(m_name))
        return StartResult::Listening;

    // Another instance may have started listening between the caller's first
    // connection attempt and now (two launches at the same time): hand it the
    // command line instead of replacing its live socket.
    if (sendMessage(message))
        return StartResult::Forwarded;

    // Nobody is listening: the socket file is left over from a crash.
    QLocalServer::removeServer(m_name);
    if (m_server.listen(m_name))
        return StartResult::Listening;

    // Two launches at the same time after a crash can both remove the stale
    // socket; the one that lost listen() forwards to the winner instead of
    // starting a second instance.
    if (sendMessage(message))
        return StartResult::Forwarded;

    return StartResult::Failed;
}

void SingleInstance::handleNewConnection()
{
    while (QLocalSocket *socket = m_server.nextPendingConnection()) {
        m_buffers.insert(socket, QByteArray());
        connect(socket, &QLocalSocket::readyRead, this, [this, socket]() {
            readFrom(socket);
        });
        connect(socket, &QLocalSocket::disconnected, this, [this, socket]() {
            m_buffers.remove(socket);
            socket->deleteLater();
        });
        // The whole message may already be waiting in the socket.
        readFrom(socket);
    }
}

void SingleInstance::readFrom(QLocalSocket *socket)
{
    const auto buffer = m_buffers.find(socket);
    if (buffer == m_buffers.end())
        return;
    buffer->append(socket->readAll());

    if (buffer->size() > kMaxMessageSize) {
        qWarning("Kondor: single-instance message too large, ignored");
        buffer->clear();
        socket->disconnectFromServer();
        return;
    }

    // One line per connection; process every complete line that arrived. The
    // sender closes the socket afterwards, so a connection without a full line
    // yet is left alone instead of being dropped before its data arrives.
    int newline = buffer->indexOf('\n');
    while (newline >= 0) {
        const QByteArray line = buffer->left(newline);
        buffer->remove(0, newline + 1);
        emit messageReceived(decodeMessage(line));
        newline = buffer->indexOf('\n');
    }
}
