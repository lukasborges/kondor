#include "extensions/extensionmanager.h"

#include <QDir>
#include <QStandardPaths>
#include <QUuid>

#include "extensions/state/extensionstorage.h"
#include "extensions/scripts/profilescripts.h"

namespace {

bool isInterruptedInstall(const QFileInfo &info)
{
    const QString name = info.fileName();
    return name.endsWith(QLatin1String(".new")) || name.endsWith(QLatin1String(".old"))
        || name.startsWith(QLatin1Char('.'));
}

QString ignoredReason(const QString &error)
{
    return error.isEmpty() ? QStringLiteral("directory name differs from id") : error;
}

}

ExtensionManager *ExtensionManager::instance()
{
    static ExtensionManager *manager = new ExtensionManager;
    return manager;
}

ExtensionManager *ExtensionManager::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(engine)
    Q_UNUSED(jsEngine)
    return instance();
}

ExtensionManager::ExtensionManager(QObject *parent)
    : QAbstractListModel(parent)
    , m_scripts(new ProfileScripts(this))
{
    reload();
}

ExtensionManager::~ExtensionManager()
{
    discardStaged();
}

QString ExtensionManager::extensionsDirectory()
{
    return QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)
        + QStringLiteral("/extensions");
}

int ExtensionManager::indexOf(const QString &id) const
{
    for (int i = 0; i < m_entries.size(); ++i) {
        if (m_entries.at(i).package.id() == id)
            return i;
    }
    return -1;
}

const InstalledExtension *ExtensionManager::find(const QString &id) const
{
    const int i = indexOf(id);
    return i < 0 ? nullptr : &m_entries.at(i);
}

InstalledExtension *ExtensionManager::find(const QString &id)
{
    const int i = indexOf(id);
    return i < 0 ? nullptr : &m_entries[i];
}

void ExtensionManager::changed()
{
    ++m_revision;
    emit revisionChanged();
    rebuildScripts();
}

InstalledExtension ExtensionManager::makeEntry(const ExtensionPackage &package) const
{
    const QString id = package.id();
    InstalledExtension entry;
    entry.package = package;
    entry.enabled = m_state.isEnabled(id);
    entry.privateAllowed = m_state.isPrivateAllowed(id);
    entry.source = m_state.source(id);
    entry.token = QUuid::createUuid().toString(QUuid::WithoutBraces);
    return entry;
}

ExtensionInstaller ExtensionManager::installer() const
{
    return ExtensionInstaller(extensionsDirectory());
}

std::optional<InstalledExtension> ExtensionManager::loadInstalled(const QFileInfo &info) const
{
    QString error;
    const ExtensionPackage package = ExtensionPackage::load(info.absoluteFilePath(), &error);
    if (package.isValid() && package.id() == info.fileName())
        return makeEntry(package);
    qWarning("Extension %s ignored: %s", qPrintable(info.fileName()),
             qPrintable(ignoredReason(error)));
    return std::nullopt;
}

QList<InstalledExtension> ExtensionManager::scanInstalled() const
{
    QList<InstalledExtension> entries;
    const QFileInfoList directories = QDir(extensionsDirectory())
        .entryInfoList(QDir::Dirs | QDir::NoDotAndDotDot, QDir::Name);
    for (const QFileInfo &info : directories) {
        if (isInterruptedInstall(info))
            QDir(info.absoluteFilePath()).removeRecursively();
        else if (const auto entry = loadInstalled(info))
            entries.append(*entry);
    }
    return entries;
}

void ExtensionManager::reload()
{
    beginResetModel();
    m_entries = scanInstalled();
    endResetModel();
    emit countChanged();
    changed();
}

void ExtensionManager::setEnabled(const QString &id, bool enabled)
{
    const int row = indexOf(id);
    if (row < 0 || m_entries.at(row).enabled == enabled)
        return;
    m_entries[row].enabled = enabled;
    m_state.setEnabled(id, enabled);
    m_state.sync();
    emit dataChanged(index(row), index(row), {EnabledRole});
    changed();
}

void ExtensionManager::removeRow(int row)
{
    beginRemoveRows(QModelIndex(), row, row);
    m_entries.removeAt(row);
    endRemoveRows();
    emit countChanged();
}

void ExtensionManager::deleteStoredData(const QString &id)
{
    QDir(extensionsDirectory() + QLatin1Char('/') + id).removeRecursively();
    m_state.removeExtension(id);
    m_state.sync();
    ExtensionStorage::removeExtension(id);
}

void ExtensionManager::remove(const QString &id)
{
    const int row = indexOf(id);
    if (row < 0)
        return;
    removeRow(row);
    deleteStoredData(id);
    emit extensionRemoved(id);
    changed();
}

void ExtensionManager::setUpdateInfo(const QString &id, bool available, bool needsReview)
{
    InstalledExtension *entry = find(id);
    if (!entry || (entry->updateAvailable == available && entry->updateNeedsReview == needsReview))
        return;
    entry->updateAvailable = available;
    entry->updateNeedsReview = needsReview;
    const int row = indexOf(id);
    emit dataChanged(index(row), index(row), {UpdateAvailableRole, UpdateNeedsReviewRole});
}
