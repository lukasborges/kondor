#pragma once

#include <QJsonObject>
#include <QNetworkAccessManager>
#include <QObject>
#include <QStringList>

#include "extensions/userscripts/userscriptpackage.h"

class UserScriptDownload;
struct InstallResult;

class UserScriptUpdater : public QObject
{
    Q_OBJECT

public:
    UserScriptUpdater(QNetworkAccessManager &network, QObject *parent);

    void checkAll();

private:
    void check(const QString &id);
    UserScriptDownload *newCheckDownload(const QString &id);
    void downloadFull(const QString &id, const QUrl &url);
    void handleChecked(const QString &id, const UserScriptSource &source);
    void install(const QString &id, const UserScriptSource &source);
    void finishUpdate(const QString &id, const InstallResult &result);

    QNetworkAccessManager &m_network;
    QStringList m_checking;
};
