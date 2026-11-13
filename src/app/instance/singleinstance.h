#pragma once

#include "app/instance/singleinstancemessage.h"

#include <QHash>
#include <QLocalServer>
#include <QObject>

class QLocalSocket;

class SingleInstance : public QObject
{
    Q_OBJECT

public:
    enum class StartResult {
        Listening,
        Forwarded,
        Failed,
    };

    explicit SingleInstance(const QString &serverName = QString(), QObject *parent = nullptr);
    ~SingleInstance() override;

    static QString serverName();

    bool sendMessage(const SingleInstanceMessage &message);
    StartResult start(const SingleInstanceMessage &message);

signals:
    void messageReceived(const SingleInstanceMessage &message);

private:
    void restrictSocketToCurrentUser();
    void handleNewConnection();
    void watch(QLocalSocket *socket);
    void readFrom(QLocalSocket *socket);
    bool bufferIncoming(QLocalSocket *socket, QByteArray &buffer);
    void emitCompleteLines(QByteArray &buffer);

    QString m_name;
    QLocalServer m_server;
    QHash<QLocalSocket *, QByteArray> m_buffers;
};
