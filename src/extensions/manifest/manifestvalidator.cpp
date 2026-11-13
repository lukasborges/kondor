#include "extensions/manifest/manifestvalidator.h"

#include <QJsonArray>
#include <QRegularExpression>

#include <algorithm>

#include "extensions/scripts/contentscriptreader.h"
#include "extensions/manifest/manifesticon.h"
#include "extensions/manifest/manifestsections.h"
#include "extensions/manifest/stringlistfield.h"

namespace {

const QStringList &requiredStringKeys()
{
    static const QStringList keys{QStringLiteral("id"), QStringLiteral("name"),
                                  QStringLiteral("version")};
    return keys;
}

const QStringList &optionalStringKeys()
{
    static const QStringList keys{QStringLiteral("description"), QStringLiteral("author"),
                                  QStringLiteral("homepage"), QStringLiteral("license"),
                                  QStringLiteral("icon")};
    return keys;
}

const QStringList &knownPermissions()
{
    static const QStringList list{QStringLiteral("tabs"), QStringLiteral("downloads"),
                                  QStringLiteral("notifications")};
    return list;
}

}

ManifestValidator::ManifestValidator(const QString &directory)
    : m_directory(directory)
{
}

std::optional<ValidManifest> ManifestValidator::validate(const QJsonObject &manifest)
{
    m_manifest = manifest;
    m_result = ValidManifest();
    if (!checkIdentity() || !checkContent())
        return std::nullopt;
    return m_result;
}

bool ManifestValidator::checkIdentity()
{
    return checkApiVersion() && checkStrings() && checkId() && checkVersion();
}

bool ManifestValidator::checkContent()
{
    return checkPermissions() && checkContentScripts() && checkSettings() && checkAction()
        && checkIcon();
}

bool ManifestValidator::checkApiVersion()
{
    const QJsonValue api = m_manifest.value(QLatin1String("kondor"));
    if (api.isUndefined())
        return fail(QStringLiteral("kondor: required"));
    if (!api.isDouble() || api.toInt() != 1)
        return fail(QStringLiteral("kondor: unsupported API version (must be 1)"));
    return true;
}

bool ManifestValidator::checkStrings()
{
    const QStringList &required = requiredStringKeys();
    const QStringList &optional = optionalStringKeys();
    return std::all_of(required.begin(), required.end(),
                       [this](const QString &key) { return checkRequiredString(key); })
        && std::all_of(optional.begin(), optional.end(),
                       [this](const QString &key) { return checkOptionalString(key); });
}

bool ManifestValidator::checkRequiredString(const QString &key)
{
    const QJsonValue value = m_manifest.value(key);
    if (value.isString() && !value.toString().isEmpty())
        return true;
    return fail(QStringLiteral("%1: required, must be a string").arg(key));
}

bool ManifestValidator::checkOptionalString(const QString &key)
{
    const QJsonValue value = m_manifest.value(key);
    if (value.isUndefined() || value.isString())
        return true;
    return fail(QStringLiteral("%1: must be a string").arg(key));
}

bool ManifestValidator::checkId()
{
    if (ExtensionPackage::isValidId(text("id")))
        return true;
    return fail(QStringLiteral("id: must match ^[a-z0-9][a-z0-9-]{1,47}$"));
}

bool ManifestValidator::checkVersion()
{
    static const QRegularExpression pattern(QStringLiteral("^\\d+\\.\\d+\\.\\d+$"));
    if (pattern.match(text("version")).hasMatch())
        return true;
    return fail(QStringLiteral("version: must be MAJOR.MINOR.PATCH"));
}

bool ManifestValidator::checkPermissions()
{
    const auto permissions = readStringList(m_manifest, {QStringLiteral("permissions")}, m_error);
    if (!permissions)
        return false;
    m_result.permissions = *permissions;
    return std::all_of(permissions->begin(), permissions->end(),
                       [this](const QString &item) { return checkKnownPermission(item); });
}

bool ManifestValidator::checkKnownPermission(const QString &permission)
{
    return knownPermissions().contains(permission)
        || fail(QStringLiteral("permissions: unknown permission: %1").arg(permission));
}

bool ManifestValidator::checkContentScripts()
{
    const QJsonValue scripts = m_manifest.value(QLatin1String("contentScripts"));
    if (!scripts.isUndefined() && !scripts.isArray())
        return fail(QStringLiteral("contentScripts: must be a list"));
    const QJsonArray array = scripts.toArray();
    for (int i = 0; i < array.size(); ++i) {
        if (!checkContentScript(array.at(i), i))
            return false;
    }
    return true;
}

bool ManifestValidator::checkContentScript(const QJsonValue &value, int index)
{
    const QString where = QStringLiteral("contentScripts[%1]").arg(index);
    if (!value.isObject())
        return fail(QStringLiteral("%1: must be an object").arg(where));
    ContentScriptReader reader(m_directory, where);
    const auto script = reader.read(value.toObject());
    if (script)
        m_result.contentScripts.append(*script);
    return script.has_value() || keepError(reader.error());
}

bool ManifestValidator::checkSettings()
{
    m_error = settingsError(m_manifest.value(QLatin1String("settings")));
    return m_error.isEmpty();
}

bool ManifestValidator::checkAction()
{
    m_error = actionError(m_manifest.value(QLatin1String("action")));
    return m_error.isEmpty();
}

bool ManifestValidator::checkIcon()
{
    const auto icon = resolveManifestIcon(m_directory, text("icon"), m_error);
    if (icon)
        m_result.iconSource = *icon;
    return icon.has_value();
}

QString ManifestValidator::text(const char *key) const
{
    return m_manifest.value(QLatin1String(key)).toString();
}

bool ManifestValidator::fail(const QString &message)
{
    return keepError(manifestError(message));
}

bool ManifestValidator::keepError(const QString &error)
{
    m_error = error;
    return false;
}
