#pragma once

#include <QByteArray>
#include <QJsonObject>
#include <QList>
#include <QString>
#include <QUrl>

#include <optional>

#include "extensions/userscripts/userscriptmetadata.h"

struct UserScriptSource {
    UserScriptMetadata metadata;
    QByteArray script;
    QList<QByteArray> requiredScripts;
    QUrl installUrl;

    bool isComplete() const { return requiredScripts.size() == metadata.requiredUrls.size(); }
};

QString userScriptId(const UserScriptMetadata &metadata);
QJsonObject userScriptManifest(const UserScriptSource &source);
QUrl userScriptDownloadUrl(const QJsonObject &userScript);
std::optional<QString> writeUserScriptPackage(const UserScriptSource &source, QString &error);
