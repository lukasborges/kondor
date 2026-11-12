#pragma once

#include <QCoreApplication>
#include <QJsonObject>
#include <QList>
#include <QString>
#include <QStringList>
#include <QUrl>
#include <QVariantList>

struct ExtensionContentScript
{
    QStringList matches;
    QStringList exclude;
    QStringList js;
    QStringList css;
    QString runAt = QStringLiteral("document-idle");
    bool allFrames = false;
};

struct ValidManifest;

class ExtensionPackage
{
    Q_DECLARE_TR_FUNCTIONS(ExtensionPackage)

public:
    static constexpr qint64 kMaxPackageBytes = 5 * 1024 * 1024;
    static constexpr int kMaxPackageFiles = 200;

    static ExtensionPackage load(const QString &directory, QString *error = nullptr);
    static bool unpack(const QString &zipPath, const QString &directory, QString *error);
    static bool isValidId(const QString &id);
    static QString localized(const QJsonObject &object, const QString &key,
                             const QString &locale = QString());
    static QVariantList permissionEntries(const QStringList &matches, const QStringList &permissions);
    static QStringList permissionLines(const QStringList &matches, const QStringList &permissions);
    static bool isSubset(const QStringList &candidate, const QStringList &allowed);

    bool isValid() const { return m_valid; }
    QString directory() const { return m_directory; }
    const QJsonObject &manifest() const { return m_manifest; }

    QString id() const { return m_manifest.value(QLatin1String("id")).toString(); }
    QString version() const { return m_manifest.value(QLatin1String("version")).toString(); }
    QString author() const { return m_manifest.value(QLatin1String("author")).toString(); }
    QString homepage() const { return m_manifest.value(QLatin1String("homepage")).toString(); }
    QString name(const QString &locale = QString()) const;
    QString description(const QString &locale = QString()) const;
    QStringList permissions() const { return m_permissions; }
    bool hasPermission(const QString &permission) const { return m_permissions.contains(permission); }
    const QList<ExtensionContentScript> &contentScripts() const { return m_contentScripts; }
    QStringList allMatches() const;

    QString iconSource() const { return m_iconSource; }

    QVariantList settingsSchema(const QString &locale = QString()) const;
    QVariantMap settingDefaults() const;
    bool hasSettings() const;

    bool hasAction() const;
    QVariantList actionItems(const QString &locale = QString()) const;
    bool actionSiteToggle() const;

    QByteArray readFile(const QString &relativePath) const;

private:
    QString readFrom(const QString &directory);
    QString validateAndKeep(const QString &directory, const QJsonObject &manifest);
    void keep(const QJsonObject &manifest, const ValidManifest &valid);

    bool m_valid = false;
    QString m_directory;
    QJsonObject m_manifest;
    QStringList m_permissions;
    QList<ExtensionContentScript> m_contentScripts;
    QString m_iconSource;
};
