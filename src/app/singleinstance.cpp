#include "app/singleinstance.h"

#include <QCryptographicHash>
#include <QDir>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLocalSocket>
#include <QStandardPaths>

namespace {
// A command line is tiny; anything bigger than this is not one of ours.
constexpr int kMaxMessageSize = 1024 * 1024;
}

SingleInstance::SingleInstance(const QString &serverName, QObject *parent)
    : QObject(parent)
    , m_name(serverName.isEmpty() ? SingleInstance::serverName() : serverName)
{
    // The socket must belong to this user only, whatever the umask: nobody
    // else may connect and receive forwarded URLs or the activation token.
    m_server.setSocketOptions(QLocalServer::UserAccessOption);
    connect(&m_server, &QLocalServer::newConnection,
            this, &SingleInstance::handleNewConnection);
}

SingleInstance::~SingleInstance() = default;

QString SingleInstance::serverName()
{
    // Per-user runtime directory (mode 0700), so no other local user can create
    // the socket first and impersonate the running instance. The hash of the
    // profile data directory gives one instance per profile: a run with an
    // isolated XDG_DATA_HOME (smoke tests, agent reviews) never forwards its
    // URLs into the real running Kondor.
    const QString dataLocation =
        QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
    const QByteArray profileHash =
        QCryptographicHash::hash(dataLocation.toUtf8(), QCryptographicHash::Sha1)
            .toHex()
            .left(16);
    QString directory = QStandardPaths::writableLocation(QStandardPaths::RuntimeLocation);
    // Inside a Flatpak sandbox $XDG_RUNTIME_DIR is private to each instance;
    // $XDG_RUNTIME_DIR/app/$FLATPAK_ID is shared by all instances of the app.
    const QString flatpakId = qEnvironmentVariable("FLATPAK_ID");
    if (!flatpakId.isEmpty()) {
        directory += QStringLiteral("/app/") + flatpakId;
        QDir().mkpath(directory);
    }
    return directory
        + QStringLiteral("/kondor-") + QString::fromLatin1(profileHash)
        + QStringLiteral(".socket");
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
    // Find the running instance by connecting, not by letting listen() fail:
    // with UserAccessOption QLocalServer binds a temporary name and renames it
    // into place, so bind() never reports EADDRINUSE and a second listen()
    // would silently take the socket name over.
    if (sendMessage(message))
        return StartResult::Forwarded;

    // Nobody is listening: the socket file is left over from a crash.
    QLocalServer::removeServer(m_name);
    if (m_server.listen(m_name))
        return StartResult::Listening;

    // Another instance won the startup race after all: hand it the command
    // line instead of running a second browser.
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
