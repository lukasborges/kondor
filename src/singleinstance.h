#pragma once

#include <QByteArray>
#include <QHash>
#include <QList>
#include <QLocalServer>
#include <QObject>
#include <QUrl>

class QLocalSocket;

// One command line handed from a later `kondor` launch to the running
// instance.
struct SingleInstanceMessage
{
    QList<QUrl> urls;
    bool privateMode = false;
    bool newWindow = false;
    QByteArray activationToken;
};

Q_DECLARE_METATYPE(SingleInstanceMessage)

// Single-instance support over a QLocalServer: one Kondor process per user
// session. A later launch sends its command line as one JSON line and exits;
// the running process opens the URLs and raises its window.
class SingleInstance : public QObject
{
    Q_OBJECT

public:
    enum class StartResult {
        Listening, // this process owns the socket and runs the app
        Forwarded, // another instance received the message; this one quits
        Failed,    // neither possible: run without single-instance support
    };

    explicit SingleInstance(const QString &serverName = QString(),
                            QObject *parent = nullptr);
    ~SingleInstance() override;

    // The socket name shared by every Kondor instance of this user.
    static QString serverName();

    // The message as one JSON line, as sent to the running instance.
    static QByteArray encodeMessage(const SingleInstanceMessage &message);
    // Parses one JSON line; invalid data yields an empty message (which only
    // raises the running window).
    static SingleInstanceMessage decodeMessage(const QByteArray &line);

    // Hands the message to the running instance. Returns true when one
    // received it, so the caller should quit.
    bool sendMessage(const SingleInstanceMessage &message);

    // Tries to become the server. When another instance won the startup race,
    // forwards the message to it instead (Forwarded) and does not listen.
    // Replaces a socket file left behind by a crash before giving up.
    StartResult start(const SingleInstanceMessage &message);

signals:
    void messageReceived(const SingleInstanceMessage &message);

private:
    void handleNewConnection();
    void readFrom(QLocalSocket *socket);

    QString m_name;
    QLocalServer m_server;
    QHash<QLocalSocket *, QByteArray> m_buffers;
};
