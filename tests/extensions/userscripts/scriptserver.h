#pragma once

#include <QHash>
#include <QHostAddress>
#include <QObject>
#include <QTcpServer>
#include <QTcpSocket>
#include <QUrl>

class ScriptServer : public QObject
{
public:
    ScriptServer()
    {
        m_server.listen(QHostAddress::LocalHost, 0);
        connect(&m_server, &QTcpServer::newConnection, this, [this]() { acceptConnections(); });
    }

    bool isListening() const { return m_server.isListening(); }

    QUrl url(const QString &path) const
    {
        return QUrl(QStringLiteral("http://127.0.0.1:%1%2").arg(m_server.serverPort()).arg(path));
    }

    void serve(const QString &path, const QByteArray &body) { m_bodies.insert(path, body); }

private:
    void acceptConnections()
    {
        while (QTcpSocket *socket = m_server.nextPendingConnection()) {
            connect(socket, &QTcpSocket::readyRead, socket, [this, socket]() { respond(socket); });
            connect(socket, &QTcpSocket::disconnected, socket, &QObject::deleteLater);
        }
    }

    void respond(QTcpSocket *socket)
    {
        const QList<QByteArray> request = socket->readAll().split(' ');
        const QString path = request.size() > 1 ? QString::fromUtf8(request.at(1)) : QString();
        const bool isKnown = m_bodies.contains(path);
        const QByteArray body = m_bodies.value(path);
        socket->write(QByteArray(isKnown ? "HTTP/1.1 200 OK" : "HTTP/1.1 404 Not Found")
                      + "\r\nContent-Type: text/javascript\r\nContent-Length: "
                      + QByteArray::number(body.size()) + "\r\nConnection: close\r\n\r\n" + body);
        socket->disconnectFromHost();
    }

    QTcpServer m_server;
    QHash<QString, QByteArray> m_bodies;
};
