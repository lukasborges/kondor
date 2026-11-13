#include "extensions/extensionmanager.h"

namespace {

using RoleReader = QVariant (*)(const InstalledExtension &entry, const QString &locale);

struct RoleDefinition {
    int role;
    const char *name;
    RoleReader read;
};

#define KONDOR_ROLE(role, name, expression) \
    {ExtensionManager::role, name, [](const InstalledExtension &e, const QString &locale) -> QVariant { \
        Q_UNUSED(locale) \
        return expression; \
    }}

const RoleDefinition kRoles[] = {
    KONDOR_ROLE(IdRole, "id", e.package.id()),
    KONDOR_ROLE(NameRole, "name", e.package.name(locale)),
    KONDOR_ROLE(DescriptionRole, "description", e.package.description(locale)),
    KONDOR_ROLE(VersionRole, "version", e.package.version()),
    KONDOR_ROLE(AuthorRole, "author", e.package.author()),
    KONDOR_ROLE(HomepageRole, "homepage", e.package.homepage()),
    KONDOR_ROLE(IconSourceRole, "iconSource", e.package.iconSource()),
    KONDOR_ROLE(EnabledRole, "enabled", e.enabled),
    KONDOR_ROLE(PrivateAllowedRole, "privateAllowed", e.privateAllowed),
    KONDOR_ROLE(PermissionsRole, "permissions",
                ExtensionPackage::permissionLines(e.package.allMatches(), e.package.permissions(),
                                                  e.package.allIncludes())),
    KONDOR_ROLE(HasSettingsRole, "hasSettings", e.package.hasSettings()),
    KONDOR_ROLE(HasActionRole, "hasAction", e.package.hasAction()),
    KONDOR_ROLE(SourceRole, "source", e.source),
    KONDOR_ROLE(UpdateAvailableRole, "updateAvailable", e.updateAvailable),
    KONDOR_ROLE(UpdateNeedsReviewRole, "updateNeedsReview", e.updateNeedsReview),
};

}

int ExtensionManager::rowCount(const QModelIndex &parent) const
{
    return parent.isValid() ? 0 : int(m_entries.size());
}

QHash<int, QByteArray> ExtensionManager::roleNames() const
{
    QHash<int, QByteArray> names;
    for (const RoleDefinition &definition : kRoles)
        names.insert(definition.role, definition.name);
    return names;
}

QVariant ExtensionManager::data(const QModelIndex &index, int role) const
{
    if (!index.isValid() || index.row() < 0 || index.row() >= m_entries.size())
        return {};
    for (const RoleDefinition &definition : kRoles) {
        if (definition.role == role)
            return definition.read(m_entries.at(index.row()), m_locale);
    }
    return {};
}
