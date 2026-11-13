#include "extensions/package/extensionpackage.h"

#include <QDir>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QRegularExpression>
#include <QSet>

#include <algorithm>

#include <optional>

#include "extensions/manifest/localizedmanifest.h"
#include "extensions/manifest/manifestvalidator.h"
#include "extensions/package/packagelimits.h"
#include "extensions/package/packagepath.h"
#include "extensions/install/permissiondescription.h"

namespace {

QString invalidJsonError(const QJsonParseError &parseError)
{
    const QString reason = parseError.error != QJsonParseError::NoError
        ? parseError.errorString() : QStringLiteral("not an object");
    return QStringLiteral("manifest.json: invalid JSON: %1").arg(reason);
}

std::optional<QJsonObject> parseManifest(const QByteArray &json, QString &error)
{
    QJsonParseError parseError;
    const QJsonDocument document = QJsonDocument::fromJson(json, &parseError);
    if (parseError.error == QJsonParseError::NoError && document.isObject())
        return document.object();
    error = invalidJsonError(parseError);
    return std::nullopt;
}

std::optional<QJsonObject> readManifest(const QString &directory, QString &error)
{
    QFile file(QDir(directory).filePath(QStringLiteral("manifest.json")));
    if (file.open(QIODevice::ReadOnly))
        return parseManifest(file.readAll(), error);
    error = QStringLiteral("manifest.json: file not found");
    return std::nullopt;
}

}

bool ExtensionPackage::isValidId(const QString &id)
{
    static const QRegularExpression pattern(QStringLiteral("^[a-z0-9][a-z0-9-]{1,47}$"));
    return pattern.match(id).hasMatch();
}

QString ExtensionPackage::localized(const QJsonObject &object, const QString &key,
                                    const QString &locale)
{
    return LocalizedManifest::localized(object, key, locale);
}

QString ExtensionPackage::name(const QString &locale) const
{
    return localized(m_manifest, QStringLiteral("name"), locale);
}

QString ExtensionPackage::description(const QString &locale) const
{
    return localized(m_manifest, QStringLiteral("description"), locale);
}

namespace {

QStringList uniqueEntries(const QList<ExtensionContentScript> &scripts,
                          QStringList ExtensionContentScript::*member)
{
    QStringList result;
    for (const ExtensionContentScript &script : scripts) {
        for (const QString &entry : script.*member) {
            if (!result.contains(entry))
                result.append(entry);
        }
    }
    return result;
}

}

QStringList ExtensionPackage::allMatches() const
{
    return uniqueEntries(m_contentScripts, &ExtensionContentScript::matches);
}

QStringList ExtensionPackage::allIncludes() const
{
    return uniqueEntries(m_contentScripts, &ExtensionContentScript::include);
}

bool ExtensionPackage::isSubset(const QStringList &candidate, const QStringList &allowed)
{
    const QSet<QString> set(allowed.begin(), allowed.end());
    return std::all_of(candidate.begin(), candidate.end(),
                       [&set](const QString &item) { return set.contains(item); });
}

QVariantList ExtensionPackage::permissionEntries(const QStringList &matches,
                                                 const QStringList &permissions,
                                                 const QStringList &includes)
{
    return PermissionDescription::permissionEntries(matches, permissions, includes);
}

QStringList ExtensionPackage::permissionLines(const QStringList &matches,
                                              const QStringList &permissions,
                                              const QStringList &includes)
{
    return PermissionDescription::permissionLines(matches, permissions, includes);
}

bool ExtensionPackage::hasSettings() const
{
    return !m_manifest.value(QLatin1String("settings")).toArray().isEmpty();
}

bool ExtensionPackage::hasAction() const
{
    const QJsonObject action = m_manifest.value(QLatin1String("action")).toObject();
    return !action.value(QLatin1String("items")).toArray().isEmpty()
        || action.value(QLatin1String("siteToggle")).toBool();
}

bool ExtensionPackage::actionSiteToggle() const
{
    return m_manifest.value(QLatin1String("action")).toObject()
        .value(QLatin1String("siteToggle")).toBool();
}

QVariantList ExtensionPackage::actionItems(const QString &locale) const
{
    return LocalizedManifest::actionItems(m_manifest, locale);
}

QVariantList ExtensionPackage::settingsSchema(const QString &locale) const
{
    return LocalizedManifest::settingsSchema(m_manifest, locale);
}

QVariantMap ExtensionPackage::settingDefaults() const
{
    return LocalizedManifest::settingDefaults(m_manifest);
}

QByteArray ExtensionPackage::readFile(const QString &relativePath) const
{
    if (!m_valid || !isSafeRelativePath(relativePath))
        return {};
    QFile file(QDir(m_directory).filePath(relativePath));
    return file.open(QIODevice::ReadOnly) ? file.readAll() : QByteArray();
}

ExtensionPackage ExtensionPackage::load(const QString &directory, QString *error)
{
    ExtensionPackage package;
    package.m_directory = QDir(directory).absolutePath();
    const QString problem = package.readFrom(directory);
    if (error && !problem.isEmpty())
        *error = problem;
    return package;
}

QString ExtensionPackage::readFrom(const QString &directory)
{
    QString error = packageLimitError(measureDirectory(directory));
    if (!error.isEmpty())
        return error;
    const std::optional<QJsonObject> manifest = readManifest(directory, error);
    return manifest ? validateAndKeep(directory, *manifest) : error;
}

QString ExtensionPackage::validateAndKeep(const QString &directory, const QJsonObject &manifest)
{
    ManifestValidator validator(directory);
    const std::optional<ValidManifest> valid = validator.validate(manifest);
    if (!valid)
        return validator.error();
    keep(manifest, *valid);
    return QString();
}

void ExtensionPackage::keep(const QJsonObject &manifest, const ValidManifest &valid)
{
    m_manifest = manifest;
    m_permissions = valid.permissions;
    m_contentScripts = valid.contentScripts;
    m_iconSource = valid.iconSource;
    m_valid = true;
}
