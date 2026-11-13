#include "extensions/extensionmanager.h"

#include <QFile>

#include "extensions/package/packagesuffix.h"

namespace {

QVariantMap failedPreview(const QString &label, const QString &error)
{
    return QVariantMap{{QStringLiteral("valid"), false},
                       {QStringLiteral("fileName"), label},
                       {QStringLiteral("error"), error}};
}

QVariantMap identityPreview(const ExtensionPackage &package, const QString &locale)
{
    return QVariantMap{
        {QStringLiteral("id"), package.id()},
        {QStringLiteral("name"), package.name(locale)},
        {QStringLiteral("version"), package.version()},
        {QStringLiteral("author"), package.author()},
        {QStringLiteral("iconSource"), package.iconSource()},
    };
}

QString localPathOf(const QString &path)
{
    return path.startsWith(QLatin1String("file:")) ? QUrl(path).toLocalFile() : path;
}

}

bool ExtensionManager::isPackageFile(const QString &path)
{
    return hasPackageSuffix(path);
}

void ExtensionManager::discardStaged()
{
    if (!m_staged)
        return;
    installer().discard(*m_staged);
    m_staged.reset();
}

QVariantMap ExtensionManager::previewOf(const StagedPackage &staged) const
{
    const ExtensionPackage &package = staged.package;
    QVariantMap preview = identityPreview(package, m_locale);
    preview.insert(QStringLiteral("valid"), true);
    preview.insert(QStringLiteral("fileName"), staged.file.label);
    preview.insert(QStringLiteral("permissions"),
                   ExtensionPackage::permissionEntries(package.allMatches(), package.permissions()));
    preview.insert(QStringLiteral("fromFile"), staged.file.source != QLatin1String("catalog"));
    preview.insert(QStringLiteral("installedVersion"), installedVersion(package.id()));
    return preview;
}

void ExtensionManager::setPending(const QVariantMap &preview)
{
    m_pendingPreview = preview;
    emit pendingInstallChanged();
}

void ExtensionManager::inspectFile(const QString &path)
{
    const QString local = localPathOf(path);
    prepareInstall({local, QStringLiteral("file"), QFileInfo(local).fileName(), false});
}

void ExtensionManager::refusePackage(const PackageFile &file, const QString &error)
{
    if (file.isTemporary)
        QFile::remove(file.zipPath);
    setPending(failedPreview(file.label, error));
}

bool ExtensionManager::prepareInstall(const PackageFile &file)
{
    discardStaged();
    QString error;
    m_staged = installer().stage(file, error);
    if (m_staged)
        setPending(previewOf(*m_staged));
    else
        refusePackage(file, error);
    return m_staged.has_value();
}

void ExtensionManager::openPackageFile(const QString &path)
{
    inspectFile(path);
    emit manageRequested();
}

void ExtensionManager::cancelInstall()
{
    discardStaged();
    if (!m_pendingPreview.isEmpty())
        setPending(QVariantMap());
}

void ExtensionManager::confirmInstall()
{
    if (!m_staged)
        return setPending(QVariantMap());
    const StagedPackage staged = *m_staged;
    m_staged.reset();
    QString error;
    const bool isInstalled = installStaged(staged, error);
    installer().discard(staged);
    setPending(isInstalled ? QVariantMap() : failedPreview(staged.file.label, error));
}

bool ExtensionManager::installStaged(const StagedPackage &staged, QString &error)
{
    return installer().commit(staged, error) && addInstalled(staged, error);
}

void ExtensionManager::appendRow(const InstalledExtension &entry)
{
    beginInsertRows(QModelIndex(), int(m_entries.size()), int(m_entries.size()));
    m_entries.append(entry);
    endInsertRows();
    emit countChanged();
}

void ExtensionManager::replaceRow(int row, const InstalledExtension &entry)
{
    m_entries[row] = entry;
    emit dataChanged(index(row), index(row));
    emit settingsChanged(entry.package.id());
}

void ExtensionManager::putEntry(const InstalledExtension &entry)
{
    const int row = indexOf(entry.package.id());
    if (row >= 0)
        replaceRow(row, entry);
    else
        appendRow(entry);
}

bool ExtensionManager::addInstalled(const StagedPackage &staged, QString &error)
{
    const QString id = staged.package.id();
    const ExtensionPackage package = ExtensionPackage::load(
        extensionsDirectory() + QLatin1Char('/') + id, &error);
    if (!package.isValid())
        return false;
    m_state.setSource(id, staged.file.source);
    m_state.sync();
    putEntry(makeEntry(package));
    changed();
    return true;
}
