#include "extensionpackage.h"

#include <QDir>
#include <QDirIterator>
#include <QFile>
#include <QFileInfo>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QLocale>
#include <QRegularExpression>
#include <QSet>
#include <QUuid>

#include <KArchive>
#include <KZip>

namespace {

const QStringList &knownPermissions()
{
    static const QStringList list{QStringLiteral("tabs"), QStringLiteral("downloads"),
                                  QStringLiteral("notifications")};
    return list;
}

const QStringList &knownSettingTypes()
{
    static const QStringList list{QStringLiteral("bool"),   QStringLiteral("number"),
                                  QStringLiteral("string"), QStringLiteral("text"),
                                  QStringLiteral("choice"), QStringLiteral("color"),
                                  QStringLiteral("keys")};
    return list;
}

// A package-relative path: no "..", no absolute path, no backslashes.
bool isSafeRelativePath(const QString &path)
{
    if (path.isEmpty() || path.startsWith(QLatin1Char('/')) || path.contains(QLatin1Char('\\'))
        || QDir::isAbsolutePath(path) || path.contains(QLatin1Char(':')))
        return false;
    const QStringList parts = path.split(QLatin1Char('/'));
    for (const QString &part : parts) {
        if (part == QLatin1String("..") || part.isEmpty())
            return false;
    }
    return true;
}

bool isHttpOrWildcardScheme(const QString &scheme)
{
    return scheme == QLatin1String("*") || scheme == QLatin1String("http")
        || scheme == QLatin1String("https");
}

struct PatternParts {
    QString scheme;
    QString host;
    bool all = false;
};

PatternParts parsePattern(const QString &pattern)
{
    PatternParts parts;
    if (pattern == QLatin1String("<all_urls>")) {
        parts.all = true;
        return parts;
    }
    const int schemeEnd = pattern.indexOf(QLatin1String("://"));
    if (schemeEnd < 0)
        return parts;
    parts.scheme = pattern.left(schemeEnd);
    const int hostStart = schemeEnd + 3;
    const int hostEnd = pattern.indexOf(QLatin1Char('/'), hostStart);
    parts.host = pattern.mid(hostStart, hostEnd < 0 ? -1 : hostEnd - hostStart);
    return parts;
}

QString fail(QString *error, const QString &message)
{
    if (error)
        *error = message;
    return message;
}

bool readStringList(const QJsonObject &object, const QString &key, const QString &path,
                    bool required, QStringList *out, QString *error)
{
    const QJsonValue value = object.value(key);
    if (value.isUndefined() || value.isNull()) {
        if (required) {
            fail(error, QStringLiteral("manifest.json: %1.%2: required").arg(path, key));
            return false;
        }
        return true;
    }
    if (!value.isArray()) {
        fail(error, QStringLiteral("manifest.json: %1.%2: must be a list of strings").arg(path, key));
        return false;
    }
    const QJsonArray array = value.toArray();
    for (int i = 0; i < array.size(); ++i) {
        if (!array.at(i).isString() || array.at(i).toString().isEmpty()) {
            fail(error, QStringLiteral("manifest.json: %1.%2[%3]: must be a non-empty string")
                            .arg(path, key).arg(i));
            return false;
        }
        out->append(array.at(i).toString());
    }
    return true;
}

} // namespace

bool ExtensionPackage::isValidId(const QString &id)
{
    static const QRegularExpression pattern(QStringLiteral("^[a-z0-9][a-z0-9-]{1,47}$"));
    return pattern.match(id).hasMatch();
}

QString ExtensionPackage::localized(const QJsonObject &object, const QString &key,
                                    const QString &locale)
{
    const QString name = locale.isEmpty() ? QLocale::system().name() : locale;
    const QStringList candidates{name, name.section(QLatin1Char('_'), 0, 0)};
    for (const QString &candidate : candidates) {
        const QJsonValue value = object.value(QStringLiteral("%1[%2]").arg(key, candidate));
        if (value.isString() && !value.toString().isEmpty())
            return value.toString();
    }
    return object.value(key).toString();
}

QString ExtensionPackage::name(const QString &locale) const
{
    return localized(m_manifest, QStringLiteral("name"), locale);
}

QString ExtensionPackage::description(const QString &locale) const
{
    return localized(m_manifest, QStringLiteral("description"), locale);
}

QStringList ExtensionPackage::allMatches() const
{
    QStringList result;
    for (const ExtensionContentScript &script : m_contentScripts) {
        for (const QString &match : script.matches) {
            if (!result.contains(match))
                result.append(match);
        }
    }
    return result;
}

bool ExtensionPackage::isSubset(const QStringList &candidate, const QStringList &allowed)
{
    const QSet<QString> set(allowed.begin(), allowed.end());
    for (const QString &item : candidate) {
        if (!set.contains(item))
            return false;
    }
    return true;
}

QVariantList ExtensionPackage::permissionEntries(const QStringList &matches,
                                                 const QStringList &permissions)
{
    QVariantList entries;
    const auto add = [&entries](const QString &icon, const QString &text) {
        entries.append(QVariantMap{{QStringLiteral("icon"), icon}, {QStringLiteral("text"), text}});
    };

    if (!matches.isEmpty()) {
        bool all = false;
        QStringList hosts;
        for (const QString &match : matches) {
            const PatternParts parts = parsePattern(match);
            if (parts.all || (isHttpOrWildcardScheme(parts.scheme) && parts.host == QLatin1String("*"))) {
                all = true;
                break;
            }
            if (!parts.host.isEmpty() && !hosts.contains(parts.host))
                hosts.append(parts.host);
        }
        if (all) {
            add(QStringLiteral("internet-services"), tr("Read and change all websites"));
        } else if (!hosts.isEmpty()) {
            QString list = hosts.mid(0, 3).join(QStringLiteral(", "));
            if (hosts.size() > 3) {
                //: %1 is a list of sites, %n the number of further sites
                list = tr("%1 and %n more", nullptr, int(hosts.size() - 3)).arg(list);
            }
            add(QStringLiteral("internet-services"), tr("Read and change pages on %1").arg(list));
        }
    }
    if (permissions.contains(QLatin1String("tabs")))
        add(QStringLiteral("tab-new"), tr("Open, close and navigate your tabs"));
    if (permissions.contains(QLatin1String("downloads")))
        add(QStringLiteral("download"), tr("Download files"));
    if (permissions.contains(QLatin1String("notifications")))
        add(QStringLiteral("notifications"), tr("Show notifications"));
    return entries;
}

QStringList ExtensionPackage::permissionLines(const QStringList &matches, const QStringList &permissions)
{
    QStringList lines;
    const QVariantList entries = permissionEntries(matches, permissions);
    for (const QVariant &entry : entries)
        lines.append(entry.toMap().value(QStringLiteral("text")).toString());
    return lines;
}

bool ExtensionPackage::hasSettings() const
{
    return !m_manifest.value(QLatin1String("settings")).toArray().isEmpty();
}

bool ExtensionPackage::hasAction() const
{
    const QJsonObject action = m_manifest.value(QLatin1String("action")).toObject();
    return !action.value(QLatin1String("items")).toArray().isEmpty()
        || action.value(QLatin1String("siteToggle")).toBool();
}

bool ExtensionPackage::actionSiteToggle() const
{
    return m_manifest.value(QLatin1String("action")).toObject()
        .value(QLatin1String("siteToggle")).toBool();
}

QVariantList ExtensionPackage::actionItems(const QString &locale) const
{
    QVariantList items;
    const QJsonArray array = m_manifest.value(QLatin1String("action")).toObject()
                                 .value(QLatin1String("items")).toArray();
    for (const QJsonValue &value : array) {
        const QJsonObject item = value.toObject();
        items.append(QVariantMap{
            {QStringLiteral("id"), item.value(QLatin1String("id")).toString()},
            {QStringLiteral("title"), localized(item, QStringLiteral("title"), locale)},
            {QStringLiteral("checkable"), item.value(QLatin1String("checkable")).toBool()},
            {QStringLiteral("icon"), item.value(QLatin1String("icon")).toString()},
        });
    }
    return items;
}

QVariantList ExtensionPackage::settingsSchema(const QString &locale) const
{
    QVariantList list;
    const QJsonArray array = m_manifest.value(QLatin1String("settings")).toArray();
    for (const QJsonValue &value : array) {
        const QJsonObject setting = value.toObject();
        QVariantMap map = setting.toVariantMap();
        map.insert(QStringLiteral("label"), localized(setting, QStringLiteral("label"), locale));
        const QJsonArray choices = setting.value(QLatin1String("choices")).toArray();
        if (!choices.isEmpty()) {
            QVariantList localizedChoices;
            for (const QJsonValue &choice : choices) {
                const QJsonObject object = choice.toObject();
                localizedChoices.append(QVariantMap{
                    {QStringLiteral("value"), object.value(QLatin1String("value")).toVariant()},
                    {QStringLiteral("label"), localized(object, QStringLiteral("label"), locale)},
                });
            }
            map.insert(QStringLiteral("choices"), localizedChoices);
        }
        list.append(map);
    }
    return list;
}

QVariantMap ExtensionPackage::settingDefaults() const
{
    QVariantMap defaults;
    const QJsonArray array = m_manifest.value(QLatin1String("settings")).toArray();
    for (const QJsonValue &value : array) {
        const QJsonObject setting = value.toObject();
        defaults.insert(setting.value(QLatin1String("key")).toString(),
                        setting.value(QLatin1String("default")).toVariant());
    }
    return defaults;
}

QByteArray ExtensionPackage::readFile(const QString &relativePath) const
{
    if (!m_valid || !isSafeRelativePath(relativePath))
        return {};
    QFile file(QDir(m_directory).filePath(relativePath));
    if (!file.open(QIODevice::ReadOnly))
        return {};
    return file.readAll();
}

ExtensionPackage ExtensionPackage::load(const QString &directory, QString *error)
{
    ExtensionPackage package;
    const QDir dir(directory);
    package.m_directory = dir.absolutePath();

    // The whole package, counted before anything is parsed.
    qint64 totalBytes = 0;
    int fileCount = 0;
    QDirIterator it(directory, QDir::Files | QDir::NoSymLinks, QDirIterator::Subdirectories);
    while (it.hasNext()) {
        it.next();
        totalBytes += it.fileInfo().size();
        ++fileCount;
    }
    if (fileCount > kMaxPackageFiles) {
        fail(error, tr("The package has more than %1 files").arg(kMaxPackageFiles));
        return package;
    }
    if (totalBytes > kMaxPackageBytes) {
        fail(error, tr("The package is larger than %1 MiB").arg(kMaxPackageBytes / (1024 * 1024)));
        return package;
    }

    QFile manifestFile(dir.filePath(QStringLiteral("manifest.json")));
    if (!manifestFile.open(QIODevice::ReadOnly)) {
        fail(error, QStringLiteral("manifest.json: file not found"));
        return package;
    }
    QJsonParseError parseError;
    const QJsonDocument document = QJsonDocument::fromJson(manifestFile.readAll(), &parseError);
    if (parseError.error != QJsonParseError::NoError || !document.isObject()) {
        fail(error, QStringLiteral("manifest.json: invalid JSON: %1")
                        .arg(parseError.error != QJsonParseError::NoError
                                 ? parseError.errorString() : QStringLiteral("not an object")));
        return package;
    }
    const QJsonObject manifest = document.object();

    // Required fields.
    const QJsonValue api = manifest.value(QLatin1String("kondor"));
    if (api.isUndefined()) {
        fail(error, QStringLiteral("manifest.json: kondor: required"));
        return package;
    }
    if (!api.isDouble() || api.toInt() != 1) {
        fail(error, QStringLiteral("manifest.json: kondor: unsupported API version (must be 1)"));
        return package;
    }
    for (const char *key : {"id", "name", "version"}) {
        const QJsonValue value = manifest.value(QLatin1String(key));
        if (!value.isString() || value.toString().isEmpty()) {
            fail(error, QStringLiteral("manifest.json: %1: required, must be a string")
                            .arg(QLatin1String(key)));
            return package;
        }
    }
    for (const char *key : {"description", "author", "homepage", "license", "icon"}) {
        const QJsonValue value = manifest.value(QLatin1String(key));
        if (!value.isUndefined() && !value.isString()) {
            fail(error, QStringLiteral("manifest.json: %1: must be a string").arg(QLatin1String(key)));
            return package;
        }
    }
    if (!isValidId(manifest.value(QLatin1String("id")).toString())) {
        fail(error, QStringLiteral("manifest.json: id: must match ^[a-z0-9][a-z0-9-]{1,47}$"));
        return package;
    }
    static const QRegularExpression versionPattern(QStringLiteral("^\\d+\\.\\d+\\.\\d+$"));
    if (!versionPattern.match(manifest.value(QLatin1String("version")).toString()).hasMatch()) {
        fail(error, QStringLiteral("manifest.json: version: must be MAJOR.MINOR.PATCH"));
        return package;
    }

    // Permissions.
    if (!readStringList(manifest, QStringLiteral("permissions"), QStringLiteral("manifest"),
                        false, &package.m_permissions, error)) {
        // readStringList already names "manifest.permissions"; keep the shorter form.
        if (error)
            error->replace(QLatin1String("manifest.json: manifest."), QLatin1String("manifest.json: "));
        return package;
    }
    for (const QString &permission : std::as_const(package.m_permissions)) {
        if (!knownPermissions().contains(permission)) {
            fail(error, QStringLiteral("manifest.json: permissions: unknown permission: %1")
                            .arg(permission));
            return package;
        }
    }

    // Files named by the manifest must exist and stay inside the package.
    const auto checkFile = [&](const QString &path, const QString &where) {
        if (!isSafeRelativePath(path)) {
            fail(error, QStringLiteral("manifest.json: %1: invalid path: %2").arg(where, path));
            return false;
        }
        const QFileInfo info(dir.filePath(path));
        if (!info.isFile() || info.isSymLink()) {
            fail(error, QStringLiteral("manifest.json: %1: file not found: %2").arg(where, path));
            return false;
        }
        return true;
    };

    const QJsonValue scripts = manifest.value(QLatin1String("contentScripts"));
    if (!scripts.isUndefined() && !scripts.isArray()) {
        fail(error, QStringLiteral("manifest.json: contentScripts: must be a list"));
        return package;
    }
    const QJsonArray scriptArray = scripts.toArray();
    for (int i = 0; i < scriptArray.size(); ++i) {
        const QString where = QStringLiteral("contentScripts[%1]").arg(i);
        if (!scriptArray.at(i).isObject()) {
            fail(error, QStringLiteral("manifest.json: %1: must be an object").arg(where));
            return package;
        }
        const QJsonObject object = scriptArray.at(i).toObject();
        ExtensionContentScript script;
        if (!readStringList(object, QStringLiteral("matches"), where, true, &script.matches, error)
            || !readStringList(object, QStringLiteral("exclude"), where, false, &script.exclude, error)
            || !readStringList(object, QStringLiteral("js"), where, false, &script.js, error)
            || !readStringList(object, QStringLiteral("css"), where, false, &script.css, error))
            return package;
        if (script.matches.isEmpty()) {
            fail(error, QStringLiteral("manifest.json: %1.matches: must not be empty").arg(where));
            return package;
        }
        if (script.js.isEmpty() && script.css.isEmpty()) {
            fail(error, QStringLiteral("manifest.json: %1: needs at least one js or css file").arg(where));
            return package;
        }
        for (const QString &file : std::as_const(script.js)) {
            if (!checkFile(file, where + QStringLiteral(".js")))
                return package;
        }
        for (const QString &file : std::as_const(script.css)) {
            if (!checkFile(file, where + QStringLiteral(".css")))
                return package;
        }
        const QJsonValue runAt = object.value(QLatin1String("runAt"));
        if (!runAt.isUndefined()) {
            const QString value = runAt.toString();
            if (value != QLatin1String("document-start") && value != QLatin1String("document-end")
                && value != QLatin1String("document-idle")) {
                fail(error, QStringLiteral("manifest.json: %1.runAt: must be document-start, "
                                           "document-end or document-idle").arg(where));
                return package;
            }
            script.runAt = value;
        }
        script.allFrames = object.value(QLatin1String("allFrames")).toBool(false);
        package.m_contentScripts.append(script);
    }

    // Settings form.
    const QJsonValue settings = manifest.value(QLatin1String("settings"));
    if (!settings.isUndefined() && !settings.isArray()) {
        fail(error, QStringLiteral("manifest.json: settings: must be a list"));
        return package;
    }
    const QJsonArray settingArray = settings.toArray();
    QSet<QString> keys;
    for (int i = 0; i < settingArray.size(); ++i) {
        const QString where = QStringLiteral("settings[%1]").arg(i);
        const QJsonObject object = settingArray.at(i).toObject();
        const QString key = object.value(QLatin1String("key")).toString();
        if (key.isEmpty() || keys.contains(key)) {
            fail(error, QStringLiteral("manifest.json: %1.key: required and unique").arg(where));
            return package;
        }
        keys.insert(key);
        if (!knownSettingTypes().contains(object.value(QLatin1String("type")).toString())) {
            fail(error, QStringLiteral("manifest.json: %1.type: unknown setting type").arg(where));
            return package;
        }
        if (object.value(QLatin1String("label")).toString().isEmpty()) {
            fail(error, QStringLiteral("manifest.json: %1.label: required").arg(where));
            return package;
        }
        if (object.value(QLatin1String("type")).toString() == QLatin1String("choice")
            && object.value(QLatin1String("choices")).toArray().isEmpty()) {
            fail(error, QStringLiteral("manifest.json: %1.choices: required for a choice").arg(where));
            return package;
        }
    }

    // Toolbar action.
    const QJsonValue action = manifest.value(QLatin1String("action"));
    if (!action.isUndefined() && !action.isObject()) {
        fail(error, QStringLiteral("manifest.json: action: must be an object"));
        return package;
    }
    const QJsonArray items = action.toObject().value(QLatin1String("items")).toArray();
    QSet<QString> itemIds;
    for (int i = 0; i < items.size(); ++i) {
        const QJsonObject item = items.at(i).toObject();
        const QString id = item.value(QLatin1String("id")).toString();
        if (id.isEmpty() || itemIds.contains(id)
            || item.value(QLatin1String("title")).toString().isEmpty()) {
            fail(error, QStringLiteral("manifest.json: action.items[%1]: needs a unique id and a title")
                            .arg(i));
            return package;
        }
        itemIds.insert(id);
    }

    // Icon: a file of the package, or a Breeze icon name.
    const QString icon = manifest.value(QLatin1String("icon")).toString();
    if (icon.isEmpty()) {
        package.m_iconSource = QStringLiteral("preferences-plugin");
    } else if (icon.endsWith(QLatin1String(".svg"), Qt::CaseInsensitive)
               || icon.endsWith(QLatin1String(".png"), Qt::CaseInsensitive)) {
        if (!checkFile(icon, QStringLiteral("icon")))
            return package;
        if (icon.endsWith(QLatin1String(".png"), Qt::CaseInsensitive)) {
            const QImage image(dir.filePath(icon));
            if (image.isNull() || image.width() < 64 || image.height() < 64) {
                fail(error, QStringLiteral("manifest.json: icon: a PNG icon must be at least 64 px: %1")
                                .arg(icon));
                return package;
            }
        }
        package.m_iconSource = QUrl::fromLocalFile(dir.filePath(icon)).toString();
    } else {
        package.m_iconSource = icon;
    }

    package.m_manifest = manifest;
    package.m_valid = true;
    return package;
}

bool ExtensionPackage::unpack(const QString &zipPath, const QString &directory, QString *error)
{
    KZip zip(zipPath);
    if (!zip.open(QIODevice::ReadOnly)) {
        fail(error, tr("The file is not a valid ZIP archive"));
        return false;
    }
    const KArchiveDirectory *root = zip.directory();
    if (!root) {
        fail(error, tr("The file is not a valid ZIP archive"));
        return false;
    }

    // Walk the archive first, so a bomb is refused before anything is written.
    struct Entry { QString path; const KArchiveFile *file; };
    QList<Entry> entries;
    qint64 total = 0;
    bool ok = true;
    QString problem;
    const auto walk = [&](auto &&self, const KArchiveDirectory *dir, const QString &prefix) -> void {
        const QStringList names = dir->entries();
        for (const QString &entryName : names) {
            if (!ok)
                return;
            const KArchiveEntry *entry = dir->entry(entryName);
            const QString path = prefix + entryName;
            if (entry->isDirectory()) {
                self(self, static_cast<const KArchiveDirectory *>(entry), path + QLatin1Char('/'));
                continue;
            }
            if (!isSafeRelativePath(path)) {
                ok = false;
                problem = tr("Unsafe file name in the package: %1").arg(path);
                return;
            }
            const auto *file = static_cast<const KArchiveFile *>(entry);
            total += file->size();
            entries.append({path, file});
            if (entries.size() > kMaxPackageFiles) {
                ok = false;
                problem = tr("The package has more than %1 files").arg(kMaxPackageFiles);
                return;
            }
            if (total > kMaxPackageBytes) {
                ok = false;
                problem = tr("The package is larger than %1 MiB").arg(kMaxPackageBytes / (1024 * 1024));
                return;
            }
        }
    };
    walk(walk, root, QString());
    if (!ok) {
        fail(error, problem);
        return false;
    }

    const QDir target(directory);
    if (!QDir().mkpath(directory)) {
        fail(error, tr("Cannot create %1").arg(directory));
        return false;
    }
    for (const Entry &entry : std::as_const(entries)) {
        if (entry.file->symLinkTarget().size() > 0)
            continue; // symbolic links are never unpacked
        const QString destination = target.filePath(entry.path);
        QDir().mkpath(QFileInfo(destination).absolutePath());
        QFile out(destination);
        if (!out.open(QIODevice::WriteOnly)) {
            fail(error, tr("Cannot write %1").arg(entry.path));
            return false;
        }
        const QByteArray data = entry.file->data();
        if (out.write(data) != data.size()) {
            fail(error, tr("Cannot write %1").arg(entry.path));
            return false;
        }
    }
    return true;
}
