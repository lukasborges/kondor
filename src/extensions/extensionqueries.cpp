#include "extensions/extensionmanager.h"

bool ExtensionManager::isInstalled(const QString &id) const
{
    return indexOf(id) >= 0;
}

QString ExtensionManager::installedVersion(const QString &id) const
{
    const InstalledExtension *entry = find(id);
    return entry ? entry->package.version() : QString();
}

QString ExtensionManager::source(const QString &id) const
{
    const InstalledExtension *entry = find(id);
    return entry ? entry->source : QString();
}

ExtensionAccess ExtensionManager::installedAccess(const QString &id) const
{
    const InstalledExtension *entry = find(id);
    if (!entry)
        return {};
    return {entry->package.allMatches(), entry->package.permissions()};
}

bool ExtensionManager::checkToken(const QString &id, const QString &token) const
{
    const InstalledExtension *entry = find(id);
    return entry && !token.isEmpty() && entry->token == token;
}

bool ExtensionManager::isActive(const QString &id, bool privateTab) const
{
    const InstalledExtension *entry = find(id);
    return entry && entry->enabled && (!privateTab || entry->privateAllowed);
}

bool ExtensionManager::hasPermission(const QString &id, const QString &permission) const
{
    const InstalledExtension *entry = find(id);
    return entry && entry->package.hasPermission(permission);
}

QString ExtensionManager::displayName(const QString &id) const
{
    const InstalledExtension *entry = find(id);
    return entry ? entry->package.name(m_locale) : id;
}
