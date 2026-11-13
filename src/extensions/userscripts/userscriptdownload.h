#pragma once

#include <QNetworkAccessManager>
#include <QObject>

#include <functional>

#include "extensions/userscripts/userscriptpackage.h"

class QNetworkReply;

class UserScriptDownload : public QObject
{
    Q_OBJECT

public:
    UserScriptDownload(QNetworkAccessManager &network, QObject *parent);

    void start(const QUrl &url);
    void startMetadataOnly(const QUrl &url);

signals:
    void finished(const UserScriptSource &source, const QString &error);

private:
    using BodyHandler = std::function<void(const QByteArray &)>;

    void fetchScript(const QUrl &url);
    void fetch(const QUrl &url, const BodyHandler &handler);
    void receive(QNetworkReply *reply, const BodyHandler &handler);
    void acceptScript(const QByteArray &body);
    void fetchNextRequirement();
    void succeed();
    void fail(const QString &error);

    QNetworkAccessManager &m_network;
    UserScriptSource m_source;
    qint64 m_remainingBytes;
    bool m_wantsRequirements = true;
    bool m_isTooLarge = false;
};
