#pragma once

#include <QCoreApplication>
#include <QJsonObject>
#include <QList>
#include <QString>
#include <QStringList>
#include <QUrl>
#include <QVariantList>

// One entry of a manifest's "contentScripts".
struct ExtensionContentScript
{
    QStringList matches;
    QStringList exclude;
    QStringList js;
    QStringList css;
    // "document-start", "document-end" or "document-idle".
    QString runAt = QStringLiteral("document-idle");
    bool allFrames = false;
};

// A Kondor extension package (#107): the unpacked contents of a .kondorext
// ZIP, validated against the manifest format of docs/extensions/api.md.
class ExtensionPackage
{
    Q_DECLARE_TR_FUNCTIONS(ExtensionPackage)

public:
    static constexpr qint64 kMaxPackageBytes = 5 * 1024 * 1024;
    static constexpr int kMaxPackageFiles = 200;

    // Reads and validates `<directory>/manifest.json` and every file it
    // names. On failure the package is invalid and `error` (when given)
    // names the first problem.
    static ExtensionPackage load(const QString &directory, QString *error = nullptr);

    // Unpacks a .kondorext file into the (new, empty) `directory`, refusing
    // archives over the size and file count limits and unsafe entry names.
    static bool unpack(const QString &zipPath, const QString &directory, QString *error);

    static bool isValidId(const QString &id);

    // `key[<locale>]` lookup: the best match for the locale ("pt_BR", then
    // "pt"), then the plain key. An empty locale uses the system locale.
    static QString localized(const QJsonObject &object, const QString &key,
                             const QString &locale = QString());

    // The lines of the install dialog and Settings: site access first, then
    // one per permission. Each entry is `{ icon, text }`.
    static QVariantList permissionEntries(const QStringList &matches, const QStringList &permissions);
    static QStringList permissionLines(const QStringList &matches, const QStringList &permissions);

    // True when every element of `candidate` is in `allowed`: the rule for
    // updating without asking the user again.
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
    // Every match pattern of every content script, without duplicates.
    QStringList allMatches() const;

    // Icon for QML: a file URL inside the package, or a Breeze icon name.
    QString iconSource() const { return m_iconSource; }

    // `[{ key, type, label, default, ... }]` with translated labels.
    QVariantList settingsSchema(const QString &locale = QString()) const;
    QVariantMap settingDefaults() const;
    bool hasSettings() const;

    bool hasAction() const;
    // `[{ id, title, checkable, icon }]` with translated titles.
    QVariantList actionItems(const QString &locale = QString()) const;
    bool actionSiteToggle() const;

    // Contents of a package file (already validated), or empty.
    QByteArray readFile(const QString &relativePath) const;

private:
    bool m_valid = false;
    QString m_directory;
    QJsonObject m_manifest;
    QStringList m_permissions;
    QList<ExtensionContentScript> m_contentScripts;
    QString m_iconSource;
};
