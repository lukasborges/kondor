#include "extensioncatalog.h"

#include <QCryptographicHash>
#include <QDir>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QStandardPaths>
#include <QTemporaryFile>
#include <QVersionNumber>

#include <functional>

#include "extensionmanager.h"
#include "extensionpackage.h"
#include "settings.h"

namespace {

const char kDefaultCatalogUrl[] = "https://lukasborges.github.io/kondor-extensions/catalog.json";
const char kContributingUrl[] = "https://github.com/lukasborges/kondor-extensions/blob/main/CONTRIBUTING.md";

QStringList stringList(const QJsonValue &value)
{
    QStringList list;
    const QJsonArray array = value.toArray();
    for (const QJsonValue &item : array) {
        if (item.isString())
            list.append(item.toString());
    }
    return list;
}

bool isNewer(const QString &candidate, const QString &installed)
{
    return QVersionNumber::fromString(candidate) > QVersionNumber::fromString(installed);
}

} // namespace

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
{
    // The model follows the installed extensions.
    ExtensionManager *manager = ExtensionManager::instance();
    connect(manager, &ExtensionManager::revisionChanged, this, &ExtensionCatalog::emitAllChanged);
    connect(manager, &QAbstractItemModel::modelReset, this, &ExtensionCatalog::emitAllChanged);
    connect(manager, &QAbstractItemModel::rowsInserted, this, &ExtensionCatalog::emitAllChanged);
    connect(manager, &QAbstractItemModel::rowsRemoved, this, &ExtensionCatalog::emitAllChanged);

    // Show the last good catalog right away.
    QFile cache(cacheFile());
    if (cache.open(QIODevice::ReadOnly)) {
        QString error;
        if (loadCatalog(cache.readAll(), &error))
            m_state = QStringLiteral("ready");
    }

    m_updateTimer.setInterval(24 * 60 * 60 * 1000);
    connect(&m_updateTimer, &QTimer::timeout, this, &ExtensionCatalog::checkForUpdates);
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
    if (!override.isEmpty())
        return QUrl(override);
    return QUrl(QLatin1String(kDefaultCatalogUrl));
}

QUrl ExtensionCatalog::contributingUrl() const
{
    return QUrl(QLatin1String(kContributingUrl));
}

int ExtensionCatalog::rowCount(const QModelIndex &parent) const
{
    return parent.isValid() ? 0 : int(m_entries.size());
}

QHash<int, QByteArray> ExtensionCatalog::roleNames() const
{
    return {
        {IdRole, "id"},
        {NameRole, "name"},
        {DescriptionRole, "description"},
        {VersionRole, "version"},
        {AuthorRole, "author"},
        {IconSourceRole, "iconSource"},
        {InstalledRole, "installed"},
        {UpdateAvailableRole, "updateAvailable"},
    };
}

QVariant ExtensionCatalog::data(const QModelIndex &index, int role) const
{
    if (!index.isValid() || index.row() < 0 || index.row() >= m_entries.size())
        return {};
    const Entry &entry = m_entries.at(index.row());
    ExtensionManager *manager = ExtensionManager::instance();
    switch (role) {
    case IdRole: return entry.id;
    case NameRole: return ExtensionPackage::localized(entry.json, QStringLiteral("name"));
    case DescriptionRole: return ExtensionPackage::localized(entry.json, QStringLiteral("description"));
    case VersionRole: return entry.version;
    case AuthorRole: return entry.json.value(QLatin1String("author")).toString();
    case IconSourceRole: return entry.iconSource;
    case InstalledRole:
        return manager->isInstalled(entry.id) && !isNewer(entry.version, manager->installedVersion(entry.id));
    case UpdateAvailableRole:
        return manager->isInstalled(entry.id) && isNewer(entry.version, manager->installedVersion(entry.id));
    }
    return {};
}

void ExtensionCatalog::emitAllChanged()
{
    if (m_entries.isEmpty())
        return;
    emit dataChanged(index(0), index(int(m_entries.size()) - 1),
                     {InstalledRole, UpdateAvailableRole});
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

const ExtensionCatalog::Entry *ExtensionCatalog::find(const QString &id) const
{
    for (const Entry &entry : m_entries) {
        if (entry.id == id)
            return &entry;
    }
    return nullptr;
}

bool ExtensionCatalog::isSilentUpdate(const QStringList &newMatches, const QStringList &newPermissions,
                                      const QStringList &oldMatches, const QStringList &oldPermissions)
{
    return ExtensionPackage::isSubset(newPermissions, oldPermissions)
        && ExtensionPackage::isSubset(newMatches, oldMatches);
}

bool ExtensionCatalog::loadCatalog(const QByteArray &json, QString *error)
{
    QJsonParseError parseError;
    const QJsonDocument document = QJsonDocument::fromJson(json, &parseError);
    if (parseError.error != QJsonParseError::NoError || !document.isObject()) {
        if (error)
            *error = tr("The catalog is not valid JSON");
        return false;
    }
    const QJsonObject root = document.object();
    if (root.value(QLatin1String("version")).toInt() != 1 || !root.value(QLatin1String("extensions")).isArray()) {
        if (error)
            *error = tr("The catalog has an unsupported format");
        return false;
    }

    // Relative URLs resolve against the catalog's own address.
    const QUrl base = catalogUrl();
    QList<Entry> entries;
    const QJsonArray array = root.value(QLatin1String("extensions")).toArray();
    for (const QJsonValue &value : array) {
        const QJsonObject object = value.toObject();
        Entry entry;
        entry.id = object.value(QLatin1String("id")).toString();
        entry.version = object.value(QLatin1String("version")).toString();
        const QString package = object.value(QLatin1String("package")).toString();
        if (!ExtensionPackage::isValidId(entry.id) || entry.version.isEmpty() || package.isEmpty())
            continue;
        entry.json = object;
        entry.matches = stringList(object.value(QLatin1String("matches")));
        entry.permissions = stringList(object.value(QLatin1String("permissions")));
        entry.package = base.resolved(QUrl(package));
        entry.sha256 = object.value(QLatin1String("sha256")).toString().toLower();
        entry.size = qint64(object.value(QLatin1String("size")).toDouble());
        const QString icon = object.value(QLatin1String("icon")).toString();
        if (icon.isEmpty())
            entry.iconSource = QStringLiteral("preferences-plugin");
        else if (icon.contains(QLatin1Char('/')) || icon.contains(QLatin1Char('.')))
            entry.iconSource = base.resolved(QUrl(icon)).toString();
        else
            entry.iconSource = icon;
        entries.append(entry);
    }

    beginResetModel();
    m_entries = entries;
    endResetModel();
    return true;
}

void ExtensionCatalog::refresh()
{
    if (m_refreshReply)
        return;
    setState(QStringLiteral("loading"));
    QNetworkRequest request(catalogUrl());
    request.setAttribute(QNetworkRequest::RedirectPolicyAttribute,
                         QNetworkRequest::NoLessSafeRedirectPolicy);
    request.setAttribute(QNetworkRequest::CacheLoadControlAttribute, QNetworkRequest::AlwaysNetwork);
    QNetworkReply *reply = m_network.get(request);
    m_refreshReply = reply;
    connect(reply, &QNetworkReply::finished, this, [this, reply]() {
        reply->deleteLater();
        if (m_refreshReply == reply)
            m_refreshReply = nullptr;
        if (reply->error() != QNetworkReply::NoError) {
            setState(m_entries.isEmpty() ? QStringLiteral("error") : QStringLiteral("ready"),
                     reply->errorString());
            emit updatesChecked();
            return;
        }
        const QByteArray body = reply->readAll();
        QString error;
        if (!loadCatalog(body, &error)) {
            setState(m_entries.isEmpty() ? QStringLiteral("error") : QStringLiteral("ready"), error);
            emit updatesChecked();
            return;
        }
        QDir().mkpath(QFileInfo(cacheFile()).absolutePath());
        QFile cache(cacheFile());
        if (cache.open(QIODevice::WriteOnly | QIODevice::Truncate))
            cache.write(body);
        setState(QStringLiteral("ready"));
        applyUpdates();
    });
}

void ExtensionCatalog::fetchPackage(const Entry &entry,
                                    std::function<void(const QString &, const QString &)> done)
{
    QNetworkRequest request(entry.package);
    request.setAttribute(QNetworkRequest::RedirectPolicyAttribute,
                         QNetworkRequest::NoLessSafeRedirectPolicy);
    QNetworkReply *reply = m_network.get(request);
    const qint64 limit = entry.size > 0 ? qMin(entry.size, kMaxPackageBytes) : kMaxPackageBytes;
    const QString expectedHash = entry.sha256;

    auto *file = new QTemporaryFile(QDir::tempPath() + QStringLiteral("/kondor-extension-XXXXXX.kondorext"),
                                    reply);
    file->setAutoRemove(false);
    if (!file->open()) {
        reply->abort();
        reply->deleteLater();
        done(QString(), tr("Cannot create a temporary file"));
        return;
    }
    const QString path = file->fileName();
    auto received = std::make_shared<qint64>(0);
    auto failed = std::make_shared<QString>();

    connect(reply, &QNetworkReply::readyRead, reply, [reply, file, limit, received, failed]() {
        const QByteArray chunk = reply->readAll();
        *received += chunk.size();
        if (*received > limit) {
            *failed = tr("The package is larger than expected");
            reply->abort();
            return;
        }
        file->write(chunk);
    });
    connect(reply, &QNetworkReply::finished, this,
            [reply, file, path, expectedHash, received, failed, done]() {
        reply->deleteLater();
        file->write(reply->readAll());
        file->close();
        const auto fail = [&](const QString &message) {
            QFile::remove(path);
            done(QString(), message);
        };
        if (!failed->isEmpty()) {
            fail(*failed);
            return;
        }
        if (reply->error() != QNetworkReply::NoError) {
            fail(reply->errorString());
            return;
        }
        QFile check(path);
        if (!check.open(QIODevice::ReadOnly)) {
            fail(tr("Cannot read the downloaded package"));
            return;
        }
        QCryptographicHash hash(QCryptographicHash::Sha256);
        hash.addData(&check);
        check.close();
        if (QString::fromLatin1(hash.result().toHex()) != expectedHash) {
            fail(tr("The downloaded package does not match its checksum"));
            return;
        }
        done(path, QString());
    });
}

void ExtensionCatalog::install(const QString &id)
{
    const Entry *entry = find(id);
    if (!entry || !m_installingId.isEmpty())
        return;
    setInstallError(QString());
    setInstalling(id);
    const QString name = ExtensionPackage::localized(entry->json, QStringLiteral("name"));
    fetchPackage(*entry, [this, id, name](const QString &path, const QString &error) {
        setInstalling(QString());
        if (path.isEmpty()) {
            setInstallError(tr("Could not download “%1”: %2").arg(name, error));
            return;
        }
        // Opens the confirmation dialog with the permissions.
        ExtensionManager::instance()->prepareInstall(path, QStringLiteral("catalog"), name, true);
    });
}

void ExtensionCatalog::startAutoUpdate()
{
    if (!m_autoUpdateConnected) {
        m_autoUpdateConnected = true;
        connect(Settings::instance(), &Settings::extensionsAutoUpdateChanged, this, [this]() {
            if (Settings::instance()->extensionsAutoUpdate()) {
                m_updateTimer.start();
                checkForUpdates();
            } else {
                m_updateTimer.stop();
            }
        });
    }
    if (!Settings::instance()->extensionsAutoUpdate())
        return;
    m_updateTimer.start();
    // A moment after startup, so the first page loads first.
    QTimer::singleShot(5000, this, &ExtensionCatalog::checkForUpdates);
}

void ExtensionCatalog::checkForUpdates()
{
    if (!Settings::instance()->extensionsAutoUpdate()) {
        m_updateTimer.stop();
        return;
    }
    // Nothing from the catalog is installed: nothing to check.
    ExtensionManager *manager = ExtensionManager::instance();
    bool any = false;
    for (int i = 0; i < manager->rowCount(); ++i) {
        const QModelIndex row = manager->index(i);
        if (manager->data(row, ExtensionManager::SourceRole).toString() == QLatin1String("catalog"))
            any = true;
    }
    if (!any) {
        emit updatesChecked();
        return;
    }
    refresh();
}

void ExtensionCatalog::applyUpdates()
{
    ExtensionManager *manager = ExtensionManager::instance();
    const bool automatic = Settings::instance()->extensionsAutoUpdate();
    for (const Entry &entry : std::as_const(m_entries)) {
        if (!manager->isInstalled(entry.id) || manager->source(entry.id) != QLatin1String("catalog"))
            continue; // file installs are never updated automatically
        if (!isNewer(entry.version, manager->installedVersion(entry.id))) {
            manager->setUpdateInfo(entry.id, false, false);
            continue;
        }
        const bool silent = isSilentUpdate(entry.matches, entry.permissions,
                                           manager->installedMatches(entry.id),
                                           manager->installedPermissions(entry.id));
        if (!silent) {
            manager->setUpdateInfo(entry.id, true, true);
            continue;
        }
        manager->setUpdateInfo(entry.id, true, false);
        if (!automatic || m_updating.contains(entry.id))
            continue;
        m_updating.append(entry.id);
        const QString id = entry.id;
        fetchPackage(entry, [this, id](const QString &path, const QString &error) {
            m_updating.removeAll(id);
            if (path.isEmpty()) {
                qWarning("Extension %s: update failed: %s", qPrintable(id), qPrintable(error));
                return;
            }
            QString installError;
            bool needsReview = false;
            ExtensionManager *manager = ExtensionManager::instance();
            if (manager->installPackage(path, QStringLiteral("catalog"), id, &installError, &needsReview))
                manager->setUpdateInfo(id, false, false);
            else if (needsReview)
                manager->setUpdateInfo(id, true, true);
            else
                qWarning("Extension %s: update failed: %s", qPrintable(id), qPrintable(installError));
            QFile::remove(path);
            emit updatesChecked();
        });
    }
    emit updatesChecked();
}
