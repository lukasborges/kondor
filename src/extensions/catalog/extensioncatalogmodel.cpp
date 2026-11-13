#include "extensions/extensioncatalog.h"

#include "extensions/extensionmanager.h"

namespace {

using RoleReader = QVariant (*)(const CatalogEntry &entry, const ExtensionManager &manager);

struct RoleDefinition {
    int role;
    const char *name;
    RoleReader read;
};

bool isInstalledAtLeast(const CatalogEntry &entry, const ExtensionManager &manager)
{
    return manager.isInstalled(entry.id)
        && !isNewerVersion(entry.version, manager.installedVersion(entry.id));
}

bool hasNewerVersion(const CatalogEntry &entry, const ExtensionManager &manager)
{
    return manager.isInstalled(entry.id)
        && isNewerVersion(entry.version, manager.installedVersion(entry.id));
}

#define KONDOR_CATALOG_ROLE(role, name, expression) \
    {ExtensionCatalog::role, name, [](const CatalogEntry &e, const ExtensionManager &manager) -> QVariant { \
        Q_UNUSED(manager) \
        return expression; \
    }}

const RoleDefinition kRoles[] = {
    KONDOR_CATALOG_ROLE(IdRole, "id", e.id),
    KONDOR_CATALOG_ROLE(NameRole, "name", ExtensionPackage::localized(e.json, QStringLiteral("name"))),
    KONDOR_CATALOG_ROLE(DescriptionRole, "description",
                        ExtensionPackage::localized(e.json, QStringLiteral("description"))),
    KONDOR_CATALOG_ROLE(VersionRole, "version", e.version),
    KONDOR_CATALOG_ROLE(AuthorRole, "author", e.json.value(QLatin1String("author")).toString()),
    KONDOR_CATALOG_ROLE(IconSourceRole, "iconSource", e.iconSource),
    KONDOR_CATALOG_ROLE(InstalledRole, "installed", isInstalledAtLeast(e, manager)),
    KONDOR_CATALOG_ROLE(UpdateAvailableRole, "updateAvailable", hasNewerVersion(e, manager)),
};

}

int ExtensionCatalog::rowCount(const QModelIndex &parent) const
{
    return parent.isValid() ? 0 : int(m_entries.size());
}

QHash<int, QByteArray> ExtensionCatalog::roleNames() const
{
    QHash<int, QByteArray> names;
    for (const RoleDefinition &definition : kRoles)
        names.insert(definition.role, definition.name);
    return names;
}

QVariant ExtensionCatalog::data(const QModelIndex &index, int role) const
{
    if (!index.isValid() || index.row() < 0 || index.row() >= m_entries.size())
        return {};
    for (const RoleDefinition &definition : kRoles) {
        if (definition.role == role)
            return definition.read(m_entries.at(index.row()), *ExtensionManager::instance());
    }
    return {};
}

void ExtensionCatalog::emitAllChanged()
{
    if (m_entries.isEmpty())
        return;
    emit dataChanged(index(0), index(int(m_entries.size()) - 1), {InstalledRole, UpdateAvailableRole});
}
