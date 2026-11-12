#pragma once

#include <QHostAddress>
#include <QObject>
#include <QTcpServer>
#include <QTcpSocket>
#include <QUrl>

class PageServer : public QObject
{
public:
    PageServer()
    {
        listen();
    }
    bool listen() { return m_server.listen(QHostAddress::LocalHost, 0); }
    int port() const { return m_server.serverPort(); }
    QUrl url(const QString &path = QStringLiteral("/")) const
    {
        return QUrl(QStringLiteral("http://127.0.0.1:%1%2").arg(port()).arg(path));
    }

    void start()
    {
        connect(&m_server, &QTcpServer::newConnection, this, [this]() { acceptConnections(); });
    }

private:
    void acceptConnections()
    {
        while (QTcpSocket *socket = m_server.nextPendingConnection())
            answerOneRequest(socket);
    }

    static void answerOneRequest(QTcpSocket *socket)
    {
        connect(socket, &QTcpSocket::readyRead, socket, [socket]() { respond(socket); });
        connect(socket, &QTcpSocket::disconnected, socket, &QObject::deleteLater);
    }

    static void respond(QTcpSocket *socket)
    {
        socket->readAll();
        const QByteArray body = "<html><head><title>t</title></head><body>page</body></html>";
        socket->write("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: "
                      + QByteArray::number(body.size()) + "\r\nConnection: close\r\n\r\n" + body);
        socket->disconnectFromHost();
    }

    QTcpServer m_server;
};
