#include "extensions/extensionmanager.h"

#include "extensions/state/extensionpins.h"

#include <algorithm>

namespace {

QString nameOf(const QVariant &entry)
{
    return entry.toMap().value(QStringLiteral("name")).toString();
}

QVariantMap actionEntry(const InstalledExtension &entry, bool isPrivate, const QString &locale)
{
    const ExtensionPackage &package = entry.package;
    return QVariantMap{
        {QStringLiteral("id"), package.id()},
        {QStringLiteral("name"), package.name(locale)},
        {QStringLiteral("iconSource"), package.iconSource()},
        {QStringLiteral("siteToggle"), package.actionSiteToggle() && !isPrivate},
        {QStringLiteral("items"), package.actionItems(locale)},
    };
}

bool hasVisibleAction(const InstalledExtension &entry, bool isPrivate)
{
    return entry.enabled && entry.package.hasAction() && (!isPrivate || entry.privateAllowed);
}

QVariantList sortedByName(QVariantList entries)
{
    std::sort(entries.begin(), entries.end(), [](const QVariant &first, const QVariant &second) {
        return nameOf(first).localeAwareCompare(nameOf(second)) < 0;
    });
    return entries;
}

}

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

QVariantList ExtensionManager::actionExtensions(bool isPrivate) const
{
    QVariantList list;
    for (const InstalledExtension &entry : m_entries) {
        if (hasVisibleAction(entry, isPrivate))
            list.append(actionEntry(entry, isPrivate, m_locale));
    }
    return sortedByName(list);
}

bool ExtensionManager::hasActionExtensions(bool isPrivate) const
{
    return !actionExtensions(isPrivate).isEmpty();
}

QVariantList ExtensionManager::pinnedActionExtensions(bool isPrivate) const
{
    return ExtensionPins::onlyPinned(actionExtensions(isPrivate));
}

bool ExtensionManager::isPinned(const QString &id) const
{
    return ExtensionPins::isPinned(id);
}

void ExtensionManager::setPinned(const QString &id, bool pinned)
{
    ExtensionPins::setPinned(id, pinned);
}
