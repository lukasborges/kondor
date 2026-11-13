#pragma once

#include <QString>
#include <QStringList>

#include <optional>

struct UserScriptMetadata {
    QString name;
    QString namespaceName;
    QString version;
    QString description;
    QString author;
    QString homepage;
    QString license;
    QString updateUrl;
    QString downloadUrl;
    QString runAt = QStringLiteral("document-idle");
    bool allFrames = true;
    bool usesResource = false;
    QStringList matches;
    QStringList includes;
    QStringList excludes;
    QStringList grants;
    QStringList requiredUrls;

    QStringList unsupportedFeatures() const;
    bool wantsNotifications() const;
};

std::optional<UserScriptMetadata> parseUserScriptMetadata(const QString &source, QString &error);
