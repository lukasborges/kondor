#include "extensions/catalog/extensioncatalog.h"

#include <QStandardPaths>

#include "extensions/catalog/catalogupdater.h"
#include "extensions/extensionmanager.h"

namespace {

const char kDefaultCatalogUrl[] = "https://lukasborges.github.io/kondor-extensions/catalog.json";
const char kContributingUrl[] = "https://github.com/lukasborges/kondor-extensions/blob/main/CONTRIBUTING.md";

}

ExtensionCatalog *ExtensionCatalog::instance()
{
    static ExtensionCatalog *catalog = new ExtensionCatalog;
    return catalog;
}

ExtensionCatalog *ExtensionCatalog::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(engine)
    Q_UNUSED(jsEngine)
    return instance();
}

ExtensionCatalog::ExtensionCatalog(QObject *parent)
    : QAbstractListModel(parent)
    , m_updater(new CatalogUpdater(this, m_network))
{
    followInstalledExtensions();
    showCachedCatalog();
    connect(m_updater, &CatalogUpdater::updatesChecked, this, &ExtensionCatalog::updatesChecked);
}

void ExtensionCatalog::followInstalledExtensions()
{
    ExtensionManager *manager = ExtensionManager::instance();
    connect(manager, &ExtensionManager::revisionChanged, this, &ExtensionCatalog::emitAllChanged);
    connect(manager, &QAbstractItemModel::modelReset, this, &ExtensionCatalog::emitAllChanged);
    connect(manager, &QAbstractItemModel::rowsInserted, this, &ExtensionCatalog::emitAllChanged);
    connect(manager, &QAbstractItemModel::rowsRemoved, this, &ExtensionCatalog::emitAllChanged);
}

void ExtensionCatalog::showCachedCatalog()
{
    QFile cache(cacheFile());
    QString error;
    if (cache.open(QIODevice::ReadOnly) && loadCatalog(cache.readAll(), &error))
        m_state = QStringLiteral("ready");
}

QString ExtensionCatalog::cacheFile()
{
    return QStandardPaths::writableLocation(QStandardPaths::CacheLocation)
        + QStringLiteral("/extensions-catalog.json");
}

QUrl ExtensionCatalog::catalogUrl() const
{
    if (m_catalogUrl.isValid())
        return m_catalogUrl;
    const QString override = qEnvironmentVariable("KONDOR_EXTENSIONS_CATALOG_URL");
    return override.isEmpty() ? QUrl(QLatin1String(kDefaultCatalogUrl)) : QUrl(override);
}

QUrl ExtensionCatalog::contributingUrl() const
{
    return QUrl(QLatin1String(kContributingUrl));
}

void ExtensionCatalog::setState(const QString &state, const QString &error)
{
    if (m_state == state && m_error == error)
        return;
    m_state = state;
    m_error = error;
    emit stateChanged();
}

void ExtensionCatalog::setInstalling(const QString &id)
{
    if (m_installingId == id)
        return;
    m_installingId = id;
    emit installingChanged();
}

void ExtensionCatalog::setInstallError(const QString &error)
{
    if (m_installError == error)
        return;
    m_installError = error;
    emit installErrorChanged();
}

const CatalogEntry *ExtensionCatalog::find(const QString &id) const
{
    for (const CatalogEntry &entry : m_entries) {
        if (entry.id == id)
            return &entry;
    }
    return nullptr;
}

bool ExtensionCatalog::isSilentUpdate(const ExtensionAccess &update, const ExtensionAccess &installed)
{
    return ExtensionPackage::isSubset(update.permissions, installed.permissions)
        && ExtensionPackage::isSubset(update.matches, installed.matches);
}

bool ExtensionCatalog::loadCatalog(const QByteArray &json, QString *error)
{
    QString problem;
    const auto entries = parseCatalog(json, catalogUrl(), problem);
    if (!entries && error)
        *error = problem;
    if (!entries)
        return false;
    beginResetModel();
    m_entries = *entries;
    endResetModel();
    return true;
}
