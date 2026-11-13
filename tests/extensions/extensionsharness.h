#pragma once

#include <QCryptographicHash>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QObject>
#include <QSignalSpy>
#include <QTemporaryDir>
#include <QTest>
#include <functional>

#include <KZip>

#include "browser/tabs/tab.h"
#include "../common/qmltesthelpers.h"
#include "core/settings/settings.h"
#include "extensions/catalog/extensioncatalog.h"
#include "extensions/extensionmanager.h"
#include "extensions/state/extensionstorage.h"
#include "passwords/passwordstore.h"

int runTestExtensionPackage(int argc, char *argv[]);
int runTestExtensionScripts(int argc, char *argv[]);
int runTestExtensionInstall(int argc, char *argv[]);
int runTestExtensionReplace(int argc, char *argv[]);
int runTestExtensionBridge(int argc, char *argv[]);
int runTestExtensionBridgeTabs(int argc, char *argv[]);
int runTestExtensionCatalog(int argc, char *argv[]);
int runTestExtensionUpdates(int argc, char *argv[]);
int runTestExtensionsUi(int argc, char *argv[]);
int runTestExtensionsPanel(int argc, char *argv[]);
int runTestPinnedToolBar(int argc, char *argv[]);
int runTestExtensionsReloadBar(int argc, char *argv[]);
int runTestExtensionPins(int argc, char *argv[]);
int runTestExtensionDialogs(int argc, char *argv[]);
int runTestExtensionPages(int argc, char *argv[]);
int runTestUserScriptPackage(int argc, char *argv[]);
int runTestUserScriptUpdate(int argc, char *argv[]);
int runTestUserScriptPages(int argc, char *argv[]);
int runTestPasswordsUi(int argc, char *argv[]);

using ManifestEdit = std::function<void(QJsonObject &)>;

inline QString dataDir(const QString &name)
{
    return QStringLiteral(KONDOR_TEST_DATA_DIR "/extensions/") + name;
}

inline bool writeFile(const QString &path, const QByteArray &content)
{
    QDir().mkpath(QFileInfo(path).absolutePath());
    QFile file(path);
    return file.open(QIODevice::WriteOnly) && file.write(content) == content.size();
}

inline bool zipDirectory(const QString &directory, const QString &zipPath)
{
    QFile::remove(zipPath);
    KZip zip(zipPath);
    if (!zip.open(QIODevice::WriteOnly))
        return false;
    const bool ok = zip.addLocalDirectory(directory, QString());
    return zip.close() && ok;
}

inline void copySampleFiles(const QString &directory)
{
    const QStringList files{QStringLiteral("content.js"), QStringLiteral("style.css"),
                            QStringLiteral("icon.svg"), QStringLiteral("manifest.json")};
    for (const QString &file : files)
        QFile::copy(dataDir(QStringLiteral("sample/") + file), directory + QLatin1Char('/') + file);
}

inline QString makeVariant(const QString &root, const QString &name, const ManifestEdit &edit)
{
    const QString directory = root + QLatin1Char('/') + name;
    QDir(directory).removeRecursively();
    QDir().mkpath(directory);
    copySampleFiles(directory);
    QFile manifest(directory + QStringLiteral("/manifest.json"));
    if (!manifest.open(QIODevice::ReadWrite))
        return QString();
    QJsonObject object = QJsonDocument::fromJson(manifest.readAll()).object();
    edit(object);
    manifest.resize(0);
    manifest.write(QJsonDocument(object).toJson());
    return directory;
}

inline QString packVariant(const QString &root, const QString &name, const ManifestEdit &edit)
{
    const QString zip = root + QLatin1Char('/') + name + QStringLiteral(".kondorext");
    const QString directory = makeVariant(root, name, edit);
    return zipDirectory(directory, zip) ? zip : QString();
}

inline QString sha256Of(const QString &path)
{
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly))
        return QString();
    return QString::fromLatin1(QCryptographicHash::hash(file.readAll(), QCryptographicHash::Sha256).toHex());
}

inline QString samplePackage(const QString &work)
{
    const QString path = work + QStringLiteral("/sample.kondorext");
    if (!QFileInfo::exists(path))
        zipDirectory(dataDir(QStringLiteral("sample")), path);
    return path;
}

inline bool installSample(const QString &work, const QString &source = QStringLiteral("file"))
{
    const InstallResult result = ExtensionManager::instance()->installPackage(
        {samplePackage(work), source}, QStringLiteral("sample"));
    if (!result.isInstalled)
        qWarning("%s", qPrintable(result.error));
    return result.isInstalled;
}

inline bool installNamed(const QString &work, const QString &id, const QString &name)
{
    const QString zip = packVariant(work, id, [&](QJsonObject &manifest) {
        manifest.insert(QStringLiteral("id"), id);
        manifest.insert(QStringLiteral("name"), name);
    });
    return ExtensionManager::instance()->installPackage({zip, QStringLiteral("file")}, id).isInstalled;
}

inline bool installPlain(const QString &work)
{
    const QJsonObject item{{QStringLiteral("id"), QStringLiteral("go")}, {QStringLiteral("title"), QStringLiteral("Go Now")}};
    const QString zip = packVariant(work, QStringLiteral("plain"), [&](QJsonObject &manifest) {
        manifest.insert(QStringLiteral("id"), QStringLiteral("plain"));
        manifest.insert(QStringLiteral("name"), QStringLiteral("Plain"));
        manifest.insert(QStringLiteral("action"), QJsonObject{{QStringLiteral("items"), QJsonArray{item}}});
    });
    return ExtensionManager::instance()->installPackage({zip, QStringLiteral("file")}, QStringLiteral("plain")).isInstalled;
}

inline void applySettings(const QString &id, const QVariantMap &settings)
{
    ExtensionManager::instance()->applyConfiguration(id, {{QStringLiteral("settings"), settings}});
}

inline void allowInPrivateWindows(const QString &id)
{
    ExtensionManager::instance()->applyConfiguration(id, {{QStringLiteral("privateAllowed"), true}});
}

inline void removeEveryExtension()
{
    ExtensionManager *manager = ExtensionManager::instance();
    manager->cancelInstall();
    while (manager->count() > 0)
        manager->remove(manager->data(manager->index(0), ExtensionManager::IdRole).toString());
    manager->setLocale(QStringLiteral("en"));
    Settings::instance()->setPinnedExtensions({});
}

inline void registerExtensionTypes()
{
    qmlRegisterUncreatableType<Tab>("Kondor", 1, 0, "Tab", QStringLiteral("test"));
    qmlRegisterUncreatableType<TabSiteReload>("Kondor", 1, 0, "TabSiteReload", QStringLiteral("test"));
    registerSingleton<ExtensionManager>("ExtensionManager");
    registerSingleton<ExtensionCatalog>("ExtensionCatalog");
    registerSingleton<PasswordStore>("PasswordStore");
    registerSingleton<Settings>("Settings");
    ExtensionManager::instance()->setLocale(QStringLiteral("en"));
}
