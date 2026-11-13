#include "app/singleinstance.h"

#include <QCryptographicHash>
#include <QDir>
#include <QLocalSocket>
#include <QStandardPaths>

namespace {
constexpr int kMaxMessageSize = 1024 * 1024;
constexpr int kSocketTimeoutMilliseconds = 500;

QString profileHash()
{
    const QString dataLocation =
        QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
    const QByteArray hash =
        QCryptographicHash::hash(dataLocation.toUtf8(), QCryptographicHash::Sha1);
    return QString::fromLatin1(hash.toHex().left(16));
}

QString runtimeDirectory()
{
    const QString directory = QStandardPaths::writableLocation(QStandardPaths::RuntimeLocation);
    const QString flatpakId = qEnvironmentVariable("FLATPAK_ID");
    if (flatpakId.isEmpty())
        return directory;
    const QString shared = directory + QStringLiteral("/app/") + flatpakId;
    QDir().mkpath(shared);
    return shared;
}

void waitUntilDisconnected(QLocalSocket &socket)
{
    socket.disconnectFromServer();
    if (socket.state() != QLocalSocket::UnconnectedState)
        socket.waitForDisconnected(kSocketTimeoutMilliseconds);
}

bool hasUnsentBytes(const QLocalSocket &socket)
{
    return socket.bytesToWrite() > 0;
}
}

SingleInstance::SingleInstance(const QString &serverName, QObject *parent)
    : QObject(parent)
    , m_name(serverName.isEmpty() ? SingleInstance::serverName() : serverName)
{
    restrictSocketToCurrentUser();
    connect(&m_server, &QLocalServer::newConnection, this, &SingleInstance::handleNewConnection);
}

SingleInstance::~SingleInstance() = default;

void SingleInstance::restrictSocketToCurrentUser()
{
    m_server.setSocketOptions(QLocalServer::UserAccessOption);
}

QString SingleInstance::serverName()
{
    return runtimeDirectory() + QStringLiteral("/kondor-") + profileHash()
        + QStringLiteral(".socket");
}

bool SingleInstance::sendMessage(const SingleInstanceMessage &message)
{
    QLocalSocket socket;
    socket.connectToServer(m_name);
    if (!socket.waitForConnected(kSocketTimeoutMilliseconds))
        return false;
    socket.write(message.toJsonLine());
    if (hasUnsentBytes(socket) && !socket.waitForBytesWritten(kSocketTimeoutMilliseconds))
        return false;
    waitUntilDisconnected(socket);
    return true;
}

SingleInstance::StartResult SingleInstance::start(const SingleInstanceMessage &message)
{
    if (sendMessage(message))
        return StartResult::Forwarded;
    QLocalServer::removeServer(m_name);
    if (m_server.listen(m_name))
        return StartResult::Listening;
    return sendMessage(message) ? StartResult::Forwarded : StartResult::Failed;
}

void SingleInstance::handleNewConnection()
{
    while (QLocalSocket *socket = m_server.nextPendingConnection())
        watch(socket);
}

void SingleInstance::watch(QLocalSocket *socket)
{
    m_buffers.insert(socket, QByteArray());
    connect(socket, &QLocalSocket::readyRead, this, [this, socket]() { readFrom(socket); });
    connect(socket, &QLocalSocket::disconnected, this, [this, socket]() {
        m_buffers.remove(socket);
        socket->deleteLater();
    });
    readFrom(socket);
}

void SingleInstance::readFrom(QLocalSocket *socket)
{
    const auto buffer = m_buffers.find(socket);
    if (buffer == m_buffers.end())
        return;
    if (bufferIncoming(socket, *buffer))
        emitCompleteLines(*buffer);
}

bool SingleInstance::bufferIncoming(QLocalSocket *socket, QByteArray &buffer)
{
    buffer.append(socket->readAll());
    if (buffer.size() <= kMaxMessageSize)
        return true;
    qWarning("Kondor: single-instance message too large, ignored");
    buffer.clear();
    socket->disconnectFromServer();
    return false;
}

void SingleInstance::emitCompleteLines(QByteArray &buffer)
{
    int newline = buffer.indexOf('\n');
    while (newline >= 0) {
        const QByteArray line = buffer.left(newline);
        buffer.remove(0, newline + 1);
        emit messageReceived(SingleInstanceMessage::fromJsonLine(line));
        newline = buffer.indexOf('\n');
    }
}
