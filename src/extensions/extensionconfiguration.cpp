#include "extensions/extensionmanager.h"

#include "extensions/state/extensionsettings.h"

namespace {

QString keyOf(const QVariantMap &setting)
{
    return setting.value(QStringLiteral("key")).toString();
}

QVariantMap withValue(const QVariant &item, const QVariantMap &values)
{
    QVariantMap setting = item.toMap();
    setting.insert(QStringLiteral("value"), values.value(keyOf(setting)));
    return setting;
}

QStringList withOrigin(QStringList sites, const QString &origin, bool isEnabled)
{
    if (isEnabled)
        sites.removeAll(origin);
    else
        sites.append(origin);
    return sites;
}

}

void ExtensionManager::applyStoredSetting(const QString &id, const QVariantMap &setting,
                                          QVariantMap &values) const
{
    const QString key = keyOf(setting);
    if (m_state.hasSetting(id, key))
        values.insert(key, sanitizeSetting(setting, m_state.setting(id, key)));
}

QVariantMap ExtensionManager::settingValues(const QString &id) const
{
    const InstalledExtension *entry = find(id);
    if (!entry)
        return {};
    QVariantMap values = entry->package.settingDefaults();
    const QVariantList schema = entry->package.settingsSchema();
    for (const QVariant &item : schema)
        applyStoredSetting(id, item.toMap(), values);
    return values;
}

QVariantList ExtensionManager::settingsWithValues(const InstalledExtension &entry) const
{
    const QVariantMap values = settingValues(entry.package.id());
    QVariantList schema = entry.package.settingsSchema(m_locale);
    for (QVariant &item : schema)
        item = withValue(item, values);
    return schema;
}

QVariantMap ExtensionManager::configurationFor(const QString &id) const
{
    const InstalledExtension *entry = find(id);
    if (!entry)
        return {};
    return QVariantMap{
        {QStringLiteral("name"), entry->package.name(m_locale)},
        {QStringLiteral("iconSource"), entry->package.iconSource()},
        {QStringLiteral("privateAllowed"), entry->privateAllowed},
        {QStringLiteral("disabledSites"), m_state.disabledSites(id)},
        {QStringLiteral("settings"), settingsWithValues(*entry)},
    };
}

bool ExtensionManager::storeSetting(const QString &id, const QVariantMap &setting,
                                    const QVariantMap &values)
{
    const QString key = keyOf(setting);
    if (!values.contains(key))
        return false;
    const QVariant value = sanitizeSetting(setting, values.value(key));
    const bool isDifferent = value != settingValues(id).value(key);
    m_state.setSetting(id, key, value);
    return isDifferent;
}

bool ExtensionManager::storeSettings(const QString &id, const QVariantMap &values)
{
    bool isDifferent = false;
    const QVariantList schema = find(id)->package.settingsSchema();
    for (const QVariant &item : schema) {
        if (storeSetting(id, item.toMap(), values))
            isDifferent = true;
    }
    return isDifferent;
}

bool ExtensionManager::storePrivateAllowed(int row, bool isAllowed)
{
    const bool isDifferent = m_entries.at(row).privateAllowed != isAllowed;
    m_entries[row].privateAllowed = isAllowed;
    m_state.setPrivateAllowed(m_entries.at(row).package.id(), isAllowed);
    return isDifferent;
}

bool ExtensionManager::storeDisabledSites(const QString &id, const QStringList &sites)
{
    const bool isDifferent = m_state.disabledSites(id) != sites;
    m_state.setDisabledSites(id, sites);
    return isDifferent;
}

ExtensionManager::ConfigurationChange ExtensionManager::storeConfiguration(
    int row, const QVariantMap &configuration)
{
    const QString id = m_entries.at(row).package.id();
    ConfigurationChange change;
    change.settings = storeSettings(id, configuration.value(QStringLiteral("settings")).toMap());
    change.privacy = storePrivateAllowed(
        row, configuration.value(QStringLiteral("privateAllowed")).toBool());
    change.sites = storeDisabledSites(
        id, configuration.value(QStringLiteral("disabledSites")).toStringList());
    m_state.sync();
    return change;
}

void ExtensionManager::applyConfiguration(const QString &id, const QVariantMap &configuration)
{
    const int row = indexOf(id);
    if (row < 0)
        return;
    const ConfigurationChange change = storeConfiguration(row, configuration);
    emit dataChanged(index(row), index(row), {PrivateAllowedRole});
    if (change.any())
        changed();
    if (change.settings)
        emit settingsChanged(id);
}

QString ExtensionManager::originOf(const QUrl &url)
{
    const bool isWebPage = url.scheme() == QLatin1String("http") || url.scheme() == QLatin1String("https");
    if (!isWebPage || url.host().isEmpty())
        return QString();
    const QString origin = url.scheme() + QStringLiteral("://") + url.host().toLower();
    return url.port() > 0 ? origin + QLatin1Char(':') + QString::number(url.port()) : origin;
}

bool ExtensionManager::siteEnabled(const QString &id, const QUrl &url) const
{
    const QString origin = originOf(url);
    return origin.isEmpty() || !m_state.disabledSites(id).contains(origin);
}

void ExtensionManager::setSiteEnabled(const QString &id, const QUrl &url, bool enabled)
{
    const QString origin = originOf(url);
    if (origin.isEmpty() || !isInstalled(id) || siteEnabled(id, url) == enabled)
        return;
    m_state.setDisabledSites(id, withOrigin(m_state.disabledSites(id), origin, enabled));
    m_state.sync();
    changed();
}
