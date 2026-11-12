#include "extensionmanager.h"

#include <QCoreApplication>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLocale>
#include <QQuickWebEngineProfile>
#include <QSqlError>
#include <QSqlQuery>
#include <QStandardPaths>
#include <QUuid>
#include <QVersionNumber>

#include "database.h"
#include "extensioncatalog.h"

namespace {

QString runtimeSource()
{
    static const QString source = []() {
        QFile file(QStringLiteral(":/scripts/extensionruntime.js"));
        if (!file.open(QIODevice::ReadOnly)) {
            qWarning("Extension runtime script not found: extensions are off");
            return QString();
        }
        return QString::fromUtf8(file.readAll());
    }();
    return source;
}

QString injectionPointName(const QString &runAt)
{
    return runAt;
}

QString compact(const QJsonObject &object)
{
    return QString::fromUtf8(QJsonDocument(object).toJson(QJsonDocument::Compact));
}

} // namespace

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
    , m_state(QStringLiteral("KDE"), QStringLiteral("Kondor"))
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

// --- Model ------------------------------------------------------------------

int ExtensionManager::rowCount(const QModelIndex &parent) const
{
    return parent.isValid() ? 0 : int(m_entries.size());
}

QHash<int, QByteArray> ExtensionManager::roleNames() const
{
    return {
        {IdRole, "id"},
        {NameRole, "name"},
        {DescriptionRole, "description"},
        {VersionRole, "version"},
        {AuthorRole, "author"},
        {HomepageRole, "homepage"},
        {IconSourceRole, "iconSource"},
        {EnabledRole, "enabled"},
        {PrivateAllowedRole, "privateAllowed"},
        {PermissionsRole, "permissions"},
        {HasSettingsRole, "hasSettings"},
        {HasActionRole, "hasAction"},
        {SourceRole, "source"},
        {UpdateAvailableRole, "updateAvailable"},
        {UpdateNeedsReviewRole, "updateNeedsReview"},
    };
}

QVariant ExtensionManager::data(const QModelIndex &index, int role) const
{
    if (!index.isValid() || index.row() < 0 || index.row() >= m_entries.size())
        return {};
    const Entry &entry = m_entries.at(index.row());
    const ExtensionPackage &package = entry.package;
    switch (role) {
    case IdRole: return package.id();
    case NameRole: return package.name(m_locale);
    case DescriptionRole: return package.description(m_locale);
    case VersionRole: return package.version();
    case AuthorRole: return package.author();
    case HomepageRole: return package.homepage();
    case IconSourceRole: return package.iconSource();
    case EnabledRole: return entry.enabled;
    case PrivateAllowedRole: return entry.privateAllowed;
    case PermissionsRole:
        return ExtensionPackage::permissionLines(package.allMatches(), package.permissions());
    case HasSettingsRole: return package.hasSettings();
    case HasActionRole: return package.hasAction();
    case SourceRole: return entry.source;
    case UpdateAvailableRole: return entry.updateAvailable;
    case UpdateNeedsReviewRole: return entry.updateNeedsReview;
    }
    return {};
}

int ExtensionManager::indexOf(const QString &id) const
{
    for (int i = 0; i < m_entries.size(); ++i) {
        if (m_entries.at(i).package.id() == id)
            return i;
    }
    return -1;
}

const ExtensionManager::Entry *ExtensionManager::find(const QString &id) const
{
    const int i = indexOf(id);
    return i < 0 ? nullptr : &m_entries.at(i);
}

ExtensionManager::Entry *ExtensionManager::find(const QString &id)
{
    const int i = indexOf(id);
    return i < 0 ? nullptr : &m_entries[i];
}

QString ExtensionManager::stateKey(const QString &id, const QString &key) const
{
    return QStringLiteral("Extensions/%1/%2").arg(id, key);
}

void ExtensionManager::changed()
{
    ++m_revision;
    emit revisionChanged();
    rebuildScripts();
}

ExtensionManager::Entry ExtensionManager::loadEntry(const ExtensionPackage &package) const
{
    Entry entry;
    entry.package = package;
    entry.enabled = m_state.value(stateKey(package.id(), QStringLiteral("Enabled")), true).toBool();
    entry.privateAllowed = m_state.value(stateKey(package.id(), QStringLiteral("PrivateAllowed")),
                                         false).toBool();
    entry.source = m_state.value(stateKey(package.id(), QStringLiteral("Source")),
                                 QStringLiteral("file")).toString();
    entry.token = QUuid::createUuid().toString(QUuid::WithoutBraces);
    return entry;
}

void ExtensionManager::reload()
{
    beginResetModel();
    m_entries.clear();
    const QDir base(extensionsDirectory());
    const QFileInfoList dirs = base.entryInfoList(QDir::Dirs | QDir::NoDotAndDotDot, QDir::Name);
    for (const QFileInfo &info : dirs) {
        // Leftovers of an interrupted install.
        if (info.fileName().endsWith(QLatin1String(".new"))
            || info.fileName().endsWith(QLatin1String(".old"))
            || info.fileName().startsWith(QLatin1Char('.'))) {
            QDir(info.absoluteFilePath()).removeRecursively();
            continue;
        }
        QString error;
        const ExtensionPackage package = ExtensionPackage::load(info.absoluteFilePath(), &error);
        if (!package.isValid() || package.id() != info.fileName()) {
            qWarning("Extension %s ignored: %s", qPrintable(info.fileName()),
                     qPrintable(error.isEmpty() ? QStringLiteral("directory name differs from id")
                                                : error));
            continue;
        }
        m_entries.append(loadEntry(package));
    }
    endResetModel();
    emit countChanged();
    changed();
}

// --- Install ----------------------------------------------------------------

bool ExtensionManager::isPackageFile(const QString &path)
{
    return path.endsWith(QLatin1String(".kondorext"), Qt::CaseInsensitive);
}

void ExtensionManager::discardStaged()
{
    if (!m_hasStaged)
        return;
    QDir(m_staged.directory).removeRecursively();
    if (m_staged.deleteZip)
        QFile::remove(m_staged.zipPath);
    m_staged = Staged();
    m_hasStaged = false;
}

bool ExtensionManager::stage(const QString &zipPath, const QString &source, Staged *out,
                             QString *error)
{
    const QString base = extensionsDirectory();
    if (!QDir().mkpath(base)) {
        if (error)
            *error = tr("Cannot create %1").arg(base);
        return false;
    }
    const QString directory = base + QStringLiteral("/.staging-")
        + QUuid::createUuid().toString(QUuid::WithoutBraces);
    if (!ExtensionPackage::unpack(zipPath, directory, error)) {
        QDir(directory).removeRecursively();
        return false;
    }
    const ExtensionPackage package = ExtensionPackage::load(directory, error);
    if (!package.isValid()) {
        QDir(directory).removeRecursively();
        return false;
    }
    out->directory = directory;
    out->package = package;
    out->source = source;
    out->zipPath = zipPath;
    return true;
}

QVariantMap ExtensionManager::previewOf(const Staged &staged, const QString &label) const
{
    const ExtensionPackage &package = staged.package;
    QVariantMap preview;
    preview.insert(QStringLiteral("valid"), true);
    preview.insert(QStringLiteral("fileName"), label);
    preview.insert(QStringLiteral("id"), package.id());
    preview.insert(QStringLiteral("name"), package.name(m_locale));
    preview.insert(QStringLiteral("version"), package.version());
    preview.insert(QStringLiteral("author"), package.author());
    preview.insert(QStringLiteral("iconSource"), package.iconSource());
    preview.insert(QStringLiteral("permissions"),
                   ExtensionPackage::permissionEntries(package.allMatches(), package.permissions()));
    preview.insert(QStringLiteral("fromFile"), staged.source != QLatin1String("catalog"));
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
    const QString local = path.startsWith(QLatin1String("file:")) ? QUrl(path).toLocalFile() : path;
    prepareInstall(local, QStringLiteral("file"), QFileInfo(local).fileName(), false);
}

bool ExtensionManager::prepareInstall(const QString &zipPath, const QString &source,
                                      const QString &label, bool deleteWhenDone)
{
    discardStaged();
    Staged staged;
    QString error;
    if (!stage(zipPath, source, &staged, &error)) {
        if (deleteWhenDone)
            QFile::remove(zipPath);
        setPending(QVariantMap{{QStringLiteral("valid"), false},
                               {QStringLiteral("fileName"), label},
                               {QStringLiteral("error"), error}});
        return false;
    }
    staged.deleteZip = deleteWhenDone;
    m_staged = staged;
    m_hasStaged = true;
    setPending(previewOf(staged, label));
    return true;
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
    if (!m_hasStaged) {
        setPending(QVariantMap());
        return;
    }
    QString error;
    Staged staged = m_staged;
    m_hasStaged = false;
    m_staged = Staged();
    const bool ok = commit(&staged, &error);
    if (staged.deleteZip)
        QFile::remove(staged.zipPath);
    if (!ok) {
        QDir(staged.directory).removeRecursively();
        setPending(QVariantMap{{QStringLiteral("valid"), false},
                               {QStringLiteral("fileName"), m_pendingPreview.value(QStringLiteral("fileName"))},
                               {QStringLiteral("error"), error}});
        return;
    }
    setPending(QVariantMap());
}

bool ExtensionManager::commit(Staged *staged, QString *error)
{
    const QString id = staged->package.id();
    const QString base = extensionsDirectory();
    const QString finalDir = base + QLatin1Char('/') + id;
    const QString newDir = finalDir + QStringLiteral(".new");
    const QString oldDir = finalDir + QStringLiteral(".old");

    QDir(newDir).removeRecursively();
    QDir(oldDir).removeRecursively();
    if (!QDir().rename(staged->directory, newDir)) {
        if (error)
            *error = tr("Cannot install into %1").arg(newDir);
        return false;
    }
    const bool replacing = QFileInfo::exists(finalDir);
    if (replacing && !QDir().rename(finalDir, oldDir)) {
        QDir(newDir).removeRecursively();
        if (error)
            *error = tr("Cannot replace %1").arg(finalDir);
        return false;
    }
    if (!QDir().rename(newDir, finalDir)) {
        if (replacing)
            QDir().rename(oldDir, finalDir);
        QDir(newDir).removeRecursively();
        if (error)
            *error = tr("Cannot install into %1").arg(finalDir);
        return false;
    }
    QDir(oldDir).removeRecursively();

    const ExtensionPackage package = ExtensionPackage::load(finalDir, error);
    if (!package.isValid())
        return false;

    m_state.setValue(stateKey(id, QStringLiteral("Source")), staged->source);
    m_state.sync();

    Entry entry = loadEntry(package);
    entry.source = staged->source;
    const int row = indexOf(id);
    if (row >= 0) {
        // Replaced: it keeps its state; the new scripts get a new token.
        m_entries[row] = entry;
        emit dataChanged(index(row), index(row));
        emit settingsChanged(id);
    } else {
        beginInsertRows(QModelIndex(), int(m_entries.size()), int(m_entries.size()));
        m_entries.append(entry);
        endInsertRows();
        emit countChanged();
    }
    changed();
    return true;
}

bool ExtensionManager::installPackage(const QString &zipPath, const QString &source,
                                      const QString &expectedId, QString *error, bool *needsReview)
{
    Staged staged;
    if (!stage(zipPath, source, &staged, error))
        return false;
    if (!expectedId.isEmpty() && staged.package.id() != expectedId) {
        QDir(staged.directory).removeRecursively();
        if (error)
            *error = tr("The package is for “%1”, not “%2”").arg(staged.package.id(), expectedId);
        return false;
    }
    if (needsReview) {
        *needsReview = false;
        if (isInstalled(expectedId)
            && !ExtensionCatalog::isSilentUpdate(staged.package.allMatches(), staged.package.permissions(),
                                                 installedMatches(expectedId), installedPermissions(expectedId))) {
            QDir(staged.directory).removeRecursively();
            *needsReview = true;
            if (error)
                *error = tr("The package asks for more permissions than the installed version");
            return false;
        }
    }
    if (!commit(&staged, error)) {
        QDir(staged.directory).removeRecursively();
        return false;
    }
    return true;
}

// --- Installed extensions ---------------------------------------------------

bool ExtensionManager::isInstalled(const QString &id) const
{
    return indexOf(id) >= 0;
}

QString ExtensionManager::installedVersion(const QString &id) const
{
    const Entry *entry = find(id);
    return entry ? entry->package.version() : QString();
}

QString ExtensionManager::source(const QString &id) const
{
    const Entry *entry = find(id);
    return entry ? entry->source : QString();
}

QStringList ExtensionManager::installedMatches(const QString &id) const
{
    const Entry *entry = find(id);
    return entry ? entry->package.allMatches() : QStringList();
}

QStringList ExtensionManager::installedPermissions(const QString &id) const
{
    const Entry *entry = find(id);
    return entry ? entry->package.permissions() : QStringList();
}

void ExtensionManager::setEnabled(const QString &id, bool enabled)
{
    const int row = indexOf(id);
    if (row < 0 || m_entries.at(row).enabled == enabled)
        return;
    m_entries[row].enabled = enabled;
    m_state.setValue(stateKey(id, QStringLiteral("Enabled")), enabled);
    m_state.sync();
    emit dataChanged(index(row), index(row), {EnabledRole});
    changed();
}

void ExtensionManager::remove(const QString &id)
{
    const int row = indexOf(id);
    if (row < 0)
        return;
    beginRemoveRows(QModelIndex(), row, row);
    m_entries.removeAt(row);
    endRemoveRows();
    emit countChanged();

    QDir(extensionsDirectory() + QLatin1Char('/') + id).removeRecursively();
    m_state.remove(QStringLiteral("Extensions/%1").arg(id));
    m_state.sync();

    QSqlDatabase db = Database::instance()->handle();
    if (Database::instance()->isValid()) {
        QSqlQuery query(db);
        query.prepare(QStringLiteral("DELETE FROM extension_storage WHERE extension_id = ?"));
        query.addBindValue(id);
        query.exec();
    }
    emit extensionRemoved(id);
    changed();
}

void ExtensionManager::setUpdateInfo(const QString &id, bool available, bool needsReview)
{
    const int row = indexOf(id);
    if (row < 0)
        return;
    Entry &entry = m_entries[row];
    if (entry.updateAvailable == available && entry.updateNeedsReview == needsReview)
        return;
    entry.updateAvailable = available;
    entry.updateNeedsReview = needsReview;
    emit dataChanged(index(row), index(row), {UpdateAvailableRole, UpdateNeedsReviewRole});
}

// --- Settings and configure dialog -------------------------------------------

QVariant ExtensionManager::sanitize(const QVariantMap &setting, const QVariant &value) const
{
    const QString type = setting.value(QStringLiteral("type")).toString();
    const QVariant fallback = setting.value(QStringLiteral("default"));
    if (type == QLatin1String("bool"))
        return value.metaType().id() == QMetaType::Bool ? value.toBool() : fallback.toBool();
    if (type == QLatin1String("number")) {
        bool ok = false;
        double number = value.toDouble(&ok);
        if (!ok)
            return fallback;
        if (setting.contains(QStringLiteral("min")))
            number = qMax(number, setting.value(QStringLiteral("min")).toDouble());
        if (setting.contains(QStringLiteral("max")))
            number = qMin(number, setting.value(QStringLiteral("max")).toDouble());
        return number;
    }
    if (type == QLatin1String("choice")) {
        const QVariantList choices = setting.value(QStringLiteral("choices")).toList();
        for (const QVariant &choice : choices) {
            if (choice.toMap().value(QStringLiteral("value")) == value)
                return value;
        }
        return fallback;
    }
    // string, text, color, keys
    return value.metaType().id() == QMetaType::QString ? value : fallback;
}

QVariantMap ExtensionManager::settingValues(const QString &id) const
{
    const Entry *entry = find(id);
    if (!entry)
        return {};
    QVariantMap values = entry->package.settingDefaults();
    const QVariantList schema = entry->package.settingsSchema();
    for (const QVariant &item : schema) {
        const QVariantMap setting = item.toMap();
        const QString key = setting.value(QStringLiteral("key")).toString();
        const QString stored = stateKey(id, QStringLiteral("Settings/") + key);
        if (m_state.contains(stored))
            values.insert(key, sanitize(setting, m_state.value(stored)));
    }
    return values;
}

QStringList ExtensionManager::disabledSites(const QString &id) const
{
    return m_state.value(stateKey(id, QStringLiteral("DisabledSites"))).toStringList();
}

QVariantMap ExtensionManager::configurationFor(const QString &id) const
{
    const Entry *entry = find(id);
    if (!entry)
        return {};
    const QVariantMap values = settingValues(id);
    QVariantList schema = entry->package.settingsSchema(m_locale);
    for (QVariant &item : schema) {
        QVariantMap setting = item.toMap();
        setting.insert(QStringLiteral("value"), values.value(setting.value(QStringLiteral("key")).toString()));
        item = setting;
    }
    return QVariantMap{
        {QStringLiteral("name"), entry->package.name(m_locale)},
        {QStringLiteral("iconSource"), entry->package.iconSource()},
        {QStringLiteral("privateAllowed"), entry->privateAllowed},
        {QStringLiteral("disabledSites"), disabledSites(id)},
        {QStringLiteral("settings"), schema},
    };
}

void ExtensionManager::applyConfiguration(const QString &id, const QVariantMap &values,
                                          bool privateAllowed, const QStringList &sites)
{
    const int row = indexOf(id);
    if (row < 0)
        return;
    Entry &entry = m_entries[row];

    const QVariantList schema = entry.package.settingsSchema();
    bool settingsDiffer = false;
    for (const QVariant &item : schema) {
        const QVariantMap setting = item.toMap();
        const QString key = setting.value(QStringLiteral("key")).toString();
        if (!values.contains(key))
            continue;
        const QVariant value = sanitize(setting, values.value(key));
        if (value != settingValues(id).value(key))
            settingsDiffer = true;
        m_state.setValue(stateKey(id, QStringLiteral("Settings/") + key), value);
    }
    const bool privacyDiffers = entry.privateAllowed != privateAllowed;
    entry.privateAllowed = privateAllowed;
    m_state.setValue(stateKey(id, QStringLiteral("PrivateAllowed")), privateAllowed);
    const bool sitesDiffer = disabledSites(id) != sites;
    if (sites.isEmpty())
        m_state.remove(stateKey(id, QStringLiteral("DisabledSites")));
    else
        m_state.setValue(stateKey(id, QStringLiteral("DisabledSites")), sites);
    m_state.sync();

    emit dataChanged(index(row), index(row), {PrivateAllowedRole});
    if (settingsDiffer || privacyDiffers || sitesDiffer)
        changed();
    if (settingsDiffer)
        emit settingsChanged(id);
}

// --- Toolbar menu -----------------------------------------------------------

QVariantList ExtensionManager::actionExtensions(bool isPrivate) const
{
    QVariantList list;
    for (const Entry &entry : m_entries) {
        if (!entry.enabled || !entry.package.hasAction() || (isPrivate && !entry.privateAllowed))
            continue;
        list.append(QVariantMap{
            {QStringLiteral("id"), entry.package.id()},
            {QStringLiteral("name"), entry.package.name(m_locale)},
            {QStringLiteral("iconSource"), entry.package.iconSource()},
            {QStringLiteral("siteToggle"), entry.package.actionSiteToggle() && !isPrivate},
            {QStringLiteral("items"), entry.package.actionItems(m_locale)},
        });
    }
    return list;
}

bool ExtensionManager::hasActionExtensions(bool isPrivate) const
{
    return !actionExtensions(isPrivate).isEmpty();
}

QString ExtensionManager::originOf(const QUrl &url)
{
    if (url.scheme() != QLatin1String("http") && url.scheme() != QLatin1String("https"))
        return QString();
    if (url.host().isEmpty())
        return QString();
    QString origin = url.scheme() + QStringLiteral("://") + url.host().toLower();
    if (url.port() > 0)
        origin += QLatin1Char(':') + QString::number(url.port());
    return origin;
}

bool ExtensionManager::siteEnabled(const QString &id, const QUrl &url) const
{
    const QString origin = originOf(url);
    return origin.isEmpty() || !disabledSites(id).contains(origin);
}

void ExtensionManager::setSiteEnabled(const QString &id, const QUrl &url, bool enabled)
{
    const QString origin = originOf(url);
    if (origin.isEmpty() || !isInstalled(id))
        return;
    QStringList sites = disabledSites(id);
    if (enabled == !sites.contains(origin))
        return;
    if (enabled)
        sites.removeAll(origin);
    else
        sites.append(origin);
    if (sites.isEmpty())
        m_state.remove(stateKey(id, QStringLiteral("DisabledSites")));
    else
        m_state.setValue(stateKey(id, QStringLiteral("DisabledSites")), sites);
    m_state.sync();
    changed();
}

// --- Content scripts --------------------------------------------------------

QWebEngineScript ExtensionManager::buildScript(const Entry &entry, int index, bool privateProfile) const
{
    const ExtensionContentScript &content = entry.package.contentScripts().at(index);
    QWebEngineScript script;
    script.setName(QStringLiteral("kondor-ext:%1:%2").arg(entry.package.id()).arg(index));
    script.setSourceCode(scriptSource(entry.package.id(), index, privateProfile));
    script.setWorldId(QWebEngineScript::ApplicationWorld);
    script.setRunsOnSubFrames(content.allFrames);
    if (content.runAt == QLatin1String("document-start"))
        script.setInjectionPoint(QWebEngineScript::DocumentCreation);
    else if (content.runAt == QLatin1String("document-end"))
        script.setInjectionPoint(QWebEngineScript::DocumentReady);
    else
        script.setInjectionPoint(QWebEngineScript::Deferred);
    return script;
}

QString ExtensionManager::scriptSource(const QString &id, int index, bool privateProfile) const
{
    const Entry *entry = find(id);
    if (!entry || index < 0 || index >= entry->package.contentScripts().size())
        return QString();
    const ExtensionPackage &package = entry->package;
    const ExtensionContentScript &content = package.contentScripts().at(index);

    QString source;
    // 1. Metadata block, read by Qt WebEngine for the match patterns.
    source += QStringLiteral("// ==UserScript==\n");
    for (const QString &match : content.matches)
        source += QStringLiteral("// @match %1\n").arg(match);
    for (const QString &exclude : content.exclude)
        source += QStringLiteral("// @exclude %1\n").arg(exclude);
    source += QStringLiteral("// @run-at %1\n").arg(injectionPointName(content.runAt));
    source += QStringLiteral("// ==/UserScript==\n");

    // 2. Closure with the extension's configuration: a snapshot of the
    // settings and the sites it is turned off on, the locale and the token.
    QJsonArray styles;
    for (const QString &file : content.css)
        styles.append(QString::fromUtf8(package.readFile(file)));
    QJsonObject config{
        {QStringLiteral("id"), package.id()},
        {QStringLiteral("version"), package.version()},
        {QStringLiteral("token"), entry->token},
        {QStringLiteral("locale"), m_locale.isEmpty() ? QLocale::system().name() : m_locale},
        {QStringLiteral("isPrivate"), privateProfile},
        {QStringLiteral("settings"), QJsonObject::fromVariantMap(settingValues(id))},
        {QStringLiteral("disabledSites"), QJsonArray::fromStringList(disabledSites(id))},
        {QStringLiteral("css"), styles},
    };

    source += QStringLiteral("(function () {\nconst __cfg = ") + compact(config) + QStringLiteral(";\n");
    source += runtimeSource();
    // 3. Site check.
    source += QStringLiteral("\nif (__cfg.disabledSites.indexOf(location.origin) !== -1)\n    return;\n");
    source += QStringLiteral("const kondor = __kondorCreateRuntime(__cfg);\n");
    // 4. CSS, as soon as the document element exists.
    source += QStringLiteral(
        "(function (styles) {\n"
        "    if (styles.length === 0) return;\n"
        "    function add() {\n"
        "        styles.forEach(function (text) {\n"
        "            const style = document.createElement(\"style\");\n"
        "            style.textContent = text;\n"
        "            document.documentElement.appendChild(style);\n"
        "        });\n"
        "    }\n"
        "    if (document.documentElement) { add(); return; }\n"
        "    new MutationObserver(function (records, observer) {\n"
        "        if (document.documentElement) { observer.disconnect(); add(); }\n"
        "    }).observe(document, { childList: true });\n"
        "})(__cfg.css);\n");
    // 5. The JavaScript files, concatenated.
    if (!content.js.isEmpty()) {
        source += QStringLiteral("(function (kondor) {\n");
        for (const QString &file : content.js)
            source += QString::fromUtf8(package.readFile(file)) + QStringLiteral("\n;\n");
        source += QStringLiteral("})(kondor);\n");
    }
    source += QStringLiteral("})();\n");
    return source;
}

QList<QWebEngineScript> ExtensionManager::scriptsFor(bool privateProfile) const
{
    QList<QWebEngineScript> scripts;
    for (const Entry &entry : m_entries) {
        if (!entry.enabled || (privateProfile && !entry.privateAllowed))
            continue;
        for (int i = 0; i < entry.package.contentScripts().size(); ++i)
            scripts.append(buildScript(entry, i, privateProfile));
    }
    return scripts;
}

void ExtensionManager::registerProfile(QQuickWebEngineProfile *profile)
{
    if (!profile)
        return;
    m_profiles.append(profile);
    connect(profile, &QObject::destroyed, this, [this, profile]() {
        m_inserted.remove(profile);
    });
    applyScripts(profile);
}

void ExtensionManager::applyScripts(QQuickWebEngineProfile *profile)
{
    QObject *collection = profile->property("userScripts").value<QObject *>();
    if (!collection)
        return;
    const QList<QWebEngineScript> old = m_inserted.take(profile);
    for (const QWebEngineScript &script : old)
        QMetaObject::invokeMethod(collection, "remove", Q_ARG(QWebEngineScript, script));
    const QList<QWebEngineScript> scripts = scriptsFor(profile->isOffTheRecord());
    for (const QWebEngineScript &script : scripts)
        QMetaObject::invokeMethod(collection, "insert", Q_ARG(QWebEngineScript, script));
    m_inserted.insert(profile, scripts);
}

void ExtensionManager::rebuildScripts()
{
    // Several changes in a row (an install touches the model, the state and
    // the scripts) rebuild once.
    if (m_rebuildQueued)
        return;
    m_rebuildQueued = true;
    QMetaObject::invokeMethod(this, [this]() {
        m_rebuildQueued = false;
        for (const QPointer<QQuickWebEngineProfile> &profile : std::as_const(m_profiles)) {
            if (profile)
                applyScripts(profile);
        }
    }, Qt::QueuedConnection);
}

// --- Page API support -------------------------------------------------------

bool ExtensionManager::checkToken(const QString &id, const QString &token) const
{
    const Entry *entry = find(id);
    return entry && !token.isEmpty() && entry->token == token;
}

bool ExtensionManager::isActive(const QString &id, bool privateTab) const
{
    const Entry *entry = find(id);
    return entry && entry->enabled && (!privateTab || entry->privateAllowed);
}

bool ExtensionManager::hasPermission(const QString &id, const QString &permission) const
{
    const Entry *entry = find(id);
    return entry && entry->package.hasPermission(permission);
}

QString ExtensionManager::displayName(const QString &id) const
{
    const Entry *entry = find(id);
    return entry ? entry->package.name(m_locale) : id;
}

QJsonValue ExtensionManager::storageGet(const QString &id, const QString &key) const
{
    if (!Database::instance()->isValid())
        return QJsonValue(QJsonValue::Null);
    QSqlQuery query(Database::instance()->handle());
    query.prepare(QStringLiteral(
        "SELECT value FROM extension_storage WHERE extension_id = ? AND key = ?"));
    query.addBindValue(id);
    query.addBindValue(key);
    if (query.exec() && query.next()) {
        const QJsonDocument document = QJsonDocument::fromJson(query.value(0).toString().toUtf8());
        if (document.isArray() && !document.array().isEmpty())
            return document.array().at(0);
    }
    return QJsonValue(QJsonValue::Null);
}

bool ExtensionManager::storageSet(const QString &id, const QString &key, const QJsonValue &value,
                                  QString *error)
{
    if (!Database::instance()->isValid()) {
        if (error)
            *error = tr("Storage is not available");
        return false;
    }
    const QString json = QString::fromUtf8(
        QJsonDocument(QJsonArray{value}).toJson(QJsonDocument::Compact));
    QSqlDatabase db = Database::instance()->handle();

    // Quota: all the other values of the extension plus this one.
    QSqlQuery used(db);
    used.prepare(QStringLiteral(
        "SELECT COALESCE(SUM(LENGTH(CAST(key AS BLOB)) + LENGTH(CAST(value AS BLOB))), 0) "
        "FROM extension_storage WHERE extension_id = ? AND key != ?"));
    used.addBindValue(id);
    used.addBindValue(key);
    qint64 total = 0;
    if (used.exec() && used.next())
        total = used.value(0).toLongLong();
    total += key.toUtf8().size() + json.toUtf8().size();
    if (total > kStorageQuota) {
        if (error)
            *error = tr("The extension's storage is full (limit: 1 MiB)");
        return false;
    }

    QSqlQuery query(db);
    query.prepare(QStringLiteral(
        "INSERT OR REPLACE INTO extension_storage (extension_id, key, value) VALUES (?, ?, ?)"));
    query.addBindValue(id);
    query.addBindValue(key);
    query.addBindValue(json);
    if (!query.exec()) {
        if (error)
            *error = query.lastError().text();
        return false;
    }
    return true;
}

void ExtensionManager::storageRemove(const QString &id, const QString &key)
{
    if (!Database::instance()->isValid())
        return;
    QSqlQuery query(Database::instance()->handle());
    query.prepare(QStringLiteral("DELETE FROM extension_storage WHERE extension_id = ? AND key = ?"));
    query.addBindValue(id);
    query.addBindValue(key);
    query.exec();
}

QStringList ExtensionManager::storageKeys(const QString &id) const
{
    QStringList keys;
    if (!Database::instance()->isValid())
        return keys;
    QSqlQuery query(Database::instance()->handle());
    query.prepare(QStringLiteral("SELECT key FROM extension_storage WHERE extension_id = ? ORDER BY key"));
    query.addBindValue(id);
    if (query.exec()) {
        while (query.next())
            keys.append(query.value(0).toString());
    }
    return keys;
}
