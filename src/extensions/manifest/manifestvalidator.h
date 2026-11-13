#pragma once

#include <QJsonObject>
#include <QString>
#include <QStringList>

#include <optional>

#include "extensions/extensionpackage.h"

struct ValidManifest {
    QStringList permissions;
    QList<ExtensionContentScript> contentScripts;
    QString iconSource;
};

class ManifestValidator
{
public:
    explicit ManifestValidator(const QString &directory);

    std::optional<ValidManifest> validate(const QJsonObject &manifest);
    QString error() const { return m_error; }

private:
    bool checkIdentity();
    bool checkContent();
    bool checkApiVersion();
    bool checkStrings();
    bool checkRequiredString(const QString &key);
    bool checkOptionalString(const QString &key);
    bool checkId();
    bool checkVersion();
    bool checkPermissions();
    bool checkKnownPermission(const QString &permission);
    bool checkContentScripts();
    bool checkContentScript(const QJsonValue &value, int index);
    bool checkSettings();
    bool checkAction();
    bool checkIcon();
    QString text(const char *key) const;
    bool fail(const QString &message);
    bool keepError(const QString &error);

    QString m_directory;
    QJsonObject m_manifest;
    ValidManifest m_result;
    QString m_error;
};
