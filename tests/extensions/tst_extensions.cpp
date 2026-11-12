#include <QCryptographicHash>
#include <QDir>
#include <QFile>
#include <QGuiApplication>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QQmlComponent>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQuickItem>
#include <QQuickStyle>
#include <QQuickWebEngineProfile>
#include <QQuickWindow>
#include <QSettings>
#include <QSignalSpy>
#include <QSqlQuery>
#include <QTcpServer>
#include <QTcpSocket>
#include <QTemporaryDir>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include <KZip>

#include "core/database.h"
#include "extensions/extensionbridge.h"
#include "extensions/extensioncatalog.h"
#include "extensions/extensionmanager.h"
#include "extensions/extensionpackage.h"
#include "browser/profilemanager.h"
#include "core/settings.h"
#include "browser/tab.h"

namespace {

QString dataDir(const QString &name)
{
    return QStringLiteral(KONDOR_TEST_DATA_DIR "/extensions/") + name;
}

bool writeFile(const QString &path, const QByteArray &content)
{
    QDir().mkpath(QFileInfo(path).absolutePath());
    QFile file(path);
    return file.open(QIODevice::WriteOnly) && file.write(content) == content.size();
}

// Packs a directory into a .kondorext file.
bool zipDirectory(const QString &directory, const QString &zipPath)
{
    QFile::remove(zipPath);
    KZip zip(zipPath);
    if (!zip.open(QIODevice::WriteOnly))
        return false;
    const bool ok = zip.addLocalDirectory(directory, QString());
    return zip.close() && ok;
}

// A copy of the sample extension with its manifest edited by `edit`.
QString makeVariant(const QString &root, const QString &name,
                    const std::function<void(QJsonObject &)> &edit)
{
    const QString directory = root + QLatin1Char('/') + name;
    QDir(directory).removeRecursively();
    QDir().mkpath(directory);
    for (const QString &file : {QStringLiteral("content.js"), QStringLiteral("style.css"),
                                QStringLiteral("icon.svg"), QStringLiteral("manifest.json")})
        QFile::copy(dataDir(QStringLiteral("sample/") + file), directory + QLatin1Char('/') + file);
    QFile manifest(directory + QStringLiteral("/manifest.json"));
    if (!manifest.open(QIODevice::ReadWrite))
        return QString();
    QJsonObject object = QJsonDocument::fromJson(manifest.readAll()).object();
    edit(object);
    manifest.resize(0);
    manifest.write(QJsonDocument(object).toJson());
    return directory;
}

QString sha256Of(const QString &path)
{
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly))
        return QString();
    return QString::fromLatin1(QCryptographicHash::hash(file.readAll(), QCryptographicHash::Sha256).toHex());
}

// Serves the same tiny page for every request on 127.0.0.1.
class PageServer : public QObject
{
public:
    PageServer()
    {
        listen();
    }
    bool listen() { return m_server.listen(QHostAddress::LocalHost, 0); }
    int port() const { return m_server.serverPort(); }
    QUrl url(const QString &path = QStringLiteral("/")) const
    {
        return QUrl(QStringLiteral("http://127.0.0.1:%1%2").arg(port()).arg(path));
    }

    void start()
    {
        connect(&m_server, &QTcpServer::newConnection, this, [this]() {
            while (QTcpSocket *socket = m_server.nextPendingConnection()) {
                connect(socket, &QTcpSocket::readyRead, socket, [socket]() {
                    socket->readAll();
                    const QByteArray body = "<html><head><title>t</title></head><body>page</body></html>";
                    socket->write("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: "
                                  + QByteArray::number(body.size()) + "\r\nConnection: close\r\n\r\n" + body);
                    socket->disconnectFromHost();
                });
                connect(socket, &QTcpSocket::disconnected, socket, &QObject::deleteLater);
            }
        });
    }

private:
    QTcpServer m_server;
};

} // namespace

class TestExtensions : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanup();

    // Package validation
    void validSample();
    void invalidFixtures_data();
    void invalidFixtures();
    void tooManyFiles();
    void tooLargePackage();
    void tooLargeArchive();
    void unsafeArchiveEntry();
    void localizedStrings();
    void permissionLines();

    // Content scripts
    void scriptMetadata();
    void runAtMapping_data();
    void runAtMapping();
    void privateProfileScripts();
    void disabledSiteIsInScript();

    // Install, update, remove
    void installFromFile();
    void invalidFileShowsError();
    void replaceKeepsState();
    void removeDeletesEverything();
    void settingsAreSanitized();

    // Storage and bridge
    void storageQuota();
    void storageIsPerExtension();
    void bridgeRejectsWrongToken();
    void bridgeEnforcesPermissions();
    void bridgeStorageReadOnlyInPrivate();
    void bridgeTabCommands();
    void bridgeOffExtension();

    // Updates and catalog
    void silentUpdateRule();
    void catalogLoadsAndInstalls();
    void catalogRejectsBadChecksum();
    void catalogRejectsOversizedPackage();
    void catalogUpdates();

    // The QML of the toolbar menu and the dialogs
    void toolbarMenuEntries();
    void configureDialogWritesValues();
    void installDialogShowsPendingInstall();
    void extensionsPageListsInstalled();

    // A real page
    void contentScriptRunsInPages();

private:
    bool installSample(const QString &source = QStringLiteral("file"));
    QString samplePackage();

    QTemporaryDir m_work;
    QQmlEngine m_engine;
};

void TestExtensions::initTestCase()
{
    QVERIFY(m_work.isValid());
    qmlRegisterUncreatableType<Tab>("Kondor", 1, 0, "Tab", QStringLiteral("test"));
    qmlRegisterSingletonType<ExtensionManager>("Kondor", 1, 0, "ExtensionManager",
                                               [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                   return ExtensionManager::instance();
                                               });
    qmlRegisterSingletonType<ExtensionCatalog>("Kondor", 1, 0, "ExtensionCatalog",
                                               [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                   return ExtensionCatalog::instance();
                                               });
    ExtensionManager::instance()->setLocale(QStringLiteral("en"));
}

void TestExtensions::cleanup()
{
    ExtensionManager *manager = ExtensionManager::instance();
    manager->cancelInstall();
    while (manager->count() > 0)
        manager->remove(manager->data(manager->index(0), ExtensionManager::IdRole).toString());
    manager->setLocale(QStringLiteral("en"));
}

QString TestExtensions::samplePackage()
{
    const QString path = m_work.path() + QStringLiteral("/sample.kondorext");
    if (!QFileInfo::exists(path))
        zipDirectory(dataDir(QStringLiteral("sample")), path);
    return path;
}

bool TestExtensions::installSample(const QString &source)
{
    QString error;
    const bool ok = ExtensionManager::instance()->installPackage(samplePackage(), source,
                                                                 QStringLiteral("sample"), &error);
    if (!ok)
        qWarning("%s", qPrintable(error));
    return ok;
}

// --- Package validation -------------------------------------------------------

void TestExtensions::validSample()
{
    QString error;
    const ExtensionPackage package = ExtensionPackage::load(dataDir(QStringLiteral("sample")), &error);
    QVERIFY2(package.isValid(), qPrintable(error));
    QCOMPARE(package.id(), QStringLiteral("sample"));
    QCOMPARE(package.version(), QStringLiteral("1.0.0"));
    QCOMPARE(package.permissions(), (QStringList{QStringLiteral("tabs"), QStringLiteral("notifications")}));
    QCOMPARE(package.contentScripts().size(), 1);
    QCOMPARE(package.contentScripts().first().runAt, QStringLiteral("document-end"));
    QVERIFY(package.hasSettings());
    QVERIFY(package.hasAction());
    QVERIFY(package.actionSiteToggle());
    QVERIFY(package.iconSource().startsWith(QLatin1String("file://")));
    QCOMPARE(package.settingDefaults().value(QStringLiteral("greeting")).toString(),
             QStringLiteral("hello"));
}

void TestExtensions::invalidFixtures_data()
{
    QTest::addColumn<QString>("fixture");
    QTest::addColumn<QString>("message");
    QTest::newRow("missing file") << QStringLiteral("missing-file")
        << QStringLiteral("manifest.json: contentScripts[0].js: file not found: content.js");
    QTest::newRow("bad id") << QStringLiteral("bad-id")
        << QStringLiteral("manifest.json: id: must match ^[a-z0-9][a-z0-9-]{1,47}$");
    QTest::newRow("dot dot") << QStringLiteral("dotdot")
        << QStringLiteral("manifest.json: contentScripts[0].js: invalid path: ../secret.js");
    QTest::newRow("no manifest") << QStringLiteral("does-not-exist")
        << QStringLiteral("manifest.json: file not found");
}

void TestExtensions::invalidFixtures()
{
    QFETCH(QString, fixture);
    QFETCH(QString, message);
    QString error;
    const ExtensionPackage package = ExtensionPackage::load(dataDir(fixture), &error);
    QVERIFY(!package.isValid());
    QCOMPARE(error, message);
}

void TestExtensions::tooManyFiles()
{
    const QString dir = makeVariant(m_work.path(), QStringLiteral("many"), [](QJsonObject &) {});
    for (int i = 0; i < ExtensionPackage::kMaxPackageFiles; ++i)
        QVERIFY(writeFile(dir + QStringLiteral("/extra/f%1.txt").arg(i), "x"));
    QString error;
    QVERIFY(!ExtensionPackage::load(dir, &error).isValid());
    QVERIFY2(error.contains(QLatin1String("200 files")), qPrintable(error));
}

void TestExtensions::tooLargePackage()
{
    const QString dir = makeVariant(m_work.path(), QStringLiteral("large"), [](QJsonObject &) {});
    QVERIFY(writeFile(dir + QStringLiteral("/big.bin"),
                      QByteArray(int(ExtensionPackage::kMaxPackageBytes) + 1, 'x')));
    QString error;
    QVERIFY(!ExtensionPackage::load(dir, &error).isValid());
    QVERIFY2(error.contains(QLatin1String("larger than 5 MiB")), qPrintable(error));
}

void TestExtensions::tooLargeArchive()
{
    const QString dir = makeVariant(m_work.path(), QStringLiteral("largezip"), [](QJsonObject &) {});
    QVERIFY(writeFile(dir + QStringLiteral("/big.bin"),
                      QByteArray(int(ExtensionPackage::kMaxPackageBytes) + 1, 'x')));
    const QString zip = m_work.path() + QStringLiteral("/large.kondorext");
    QVERIFY(zipDirectory(dir, zip));
    QString error;
    QVERIFY(!ExtensionPackage::unpack(zip, m_work.path() + QStringLiteral("/unpacked-large"), &error));
    QVERIFY2(error.contains(QLatin1String("larger than 5 MiB")), qPrintable(error));
    QVERIFY(!QFileInfo::exists(m_work.path() + QStringLiteral("/unpacked-large/big.bin")));
}

void TestExtensions::unsafeArchiveEntry()
{
    // An archive entry that climbs out of the install directory.
    const QString zipPath = m_work.path() + QStringLiteral("/unsafe.kondorext");
    QFile::remove(zipPath);
    {
        KZip zip(zipPath);
        QVERIFY(zip.open(QIODevice::WriteOnly));
        QVERIFY(zip.writeFile(QStringLiteral("manifest.json"), QByteArray("{}")));
        QVERIFY(zip.writeFile(QStringLiteral("../evil.js"), QByteArray("x")));
        QVERIFY(zip.close());
    }
    QString error;
    const QString target = m_work.path() + QStringLiteral("/unpacked-unsafe");
    QVERIFY(!ExtensionPackage::unpack(zipPath, target, &error));
    QVERIFY2(error.contains(QLatin1String("Unsafe file name")), qPrintable(error));
    QVERIFY(!QFileInfo::exists(m_work.path() + QStringLiteral("/evil.js")));
}

void TestExtensions::localizedStrings()
{
    const ExtensionPackage package = ExtensionPackage::load(dataDir(QStringLiteral("sample")));
    QCOMPARE(package.name(QStringLiteral("pt_BR")), QStringLiteral("Extensão de Exemplo"));
    QCOMPARE(package.name(QStringLiteral("pt_PT")), QStringLiteral("Sample Extension"));
    QCOMPARE(package.name(QStringLiteral("de")), QStringLiteral("Sample Extension"));
    const QVariantList settings = package.settingsSchema(QStringLiteral("pt_BR"));
    QCOMPARE(settings.first().toMap().value(QStringLiteral("label")).toString(), QStringLiteral("Saudação"));
    QCOMPARE(package.actionItems(QStringLiteral("pt_BR")).first().toMap().value(QStringLiteral("title")).toString(),
             QStringLiteral("Alternar Marca"));
}

void TestExtensions::permissionLines()
{
    const QStringList all{QStringLiteral("https://*/*"), QStringLiteral("http://*/*")};
    QCOMPARE(ExtensionPackage::permissionLines(all, {}),
             (QStringList{QStringLiteral("Read and change all websites")}));
    QCOMPARE(ExtensionPackage::permissionLines({QStringLiteral("<all_urls>")}, {}).size(), 1);

    QCOMPARE(ExtensionPackage::permissionLines({QStringLiteral("*://www.youtube.com/*")}, {}),
             (QStringList{QStringLiteral("Read and change pages on www.youtube.com")}));

    const QStringList many{QStringLiteral("https://a.com/*"), QStringLiteral("https://b.com/*"),
                           QStringLiteral("https://c.com/*"), QStringLiteral("https://d.com/*"),
                           QStringLiteral("https://e.com/*")};
    QCOMPARE(ExtensionPackage::permissionLines(many, {}).first(),
             QStringLiteral("Read and change pages on a.com, b.com, c.com and 2 more"));

    const QStringList lines = ExtensionPackage::permissionLines(
        {QStringLiteral("<all_urls>")},
        {QStringLiteral("tabs"), QStringLiteral("downloads"), QStringLiteral("notifications")});
    QCOMPARE(lines.size(), 4);
    QCOMPARE(lines.at(1), QStringLiteral("Open, close and navigate your tabs"));
    QCOMPARE(lines.at(2), QStringLiteral("Download files"));
    QCOMPARE(lines.at(3), QStringLiteral("Show notifications"));
}

// --- Content scripts -----------------------------------------------------------

void TestExtensions::scriptMetadata()
{
    QVERIFY(installSample());
    ExtensionManager *manager = ExtensionManager::instance();
    const QString source = manager->scriptSource(QStringLiteral("sample"), 0, false);
    // The metadata block comes first, for Qt WebEngine's match patterns.
    QVERIFY(source.startsWith(QStringLiteral("// ==UserScript==\n")));
    QVERIFY(source.contains(QStringLiteral("// @match *://127.0.0.1/*\n")));
    QVERIFY(source.contains(QStringLiteral("// @match *://localhost/*\n")));
    QVERIFY(source.contains(QStringLiteral("// @exclude *://127.0.0.1:*/excluded/*\n")));
    QVERIFY(source.contains(QStringLiteral("// @run-at document-end\n// ==/UserScript==\n")));
    // The CSS and the extension's JavaScript are in the script.
    QVERIFY(source.contains(QStringLiteral("border-top: 4px solid #3daee9")));
    QVERIFY(source.contains(QStringLiteral("data-kondor-sample")));
    QVERIFY(source.contains(QStringLiteral("__kondorCreateRuntime")));
    // The token is generated per run and never repeated across extensions.
    QVERIFY(!source.contains(QStringLiteral("\"token\":\"\"")));

    const QList<QWebEngineScript> scripts = manager->scriptsFor(false);
    QCOMPARE(scripts.size(), 1);
    QCOMPARE(scripts.first().name(), QStringLiteral("kondor-ext:sample:0"));
    QCOMPARE(scripts.first().worldId(), uint(QWebEngineScript::ApplicationWorld));
    QVERIFY(!scripts.first().runsOnSubFrames());
}

void TestExtensions::runAtMapping_data()
{
    QTest::addColumn<QString>("runAt");
    QTest::addColumn<int>("point");
    QTest::newRow("start") << QStringLiteral("document-start") << int(QWebEngineScript::DocumentCreation);
    QTest::newRow("end") << QStringLiteral("document-end") << int(QWebEngineScript::DocumentReady);
    QTest::newRow("idle") << QStringLiteral("document-idle") << int(QWebEngineScript::Deferred);
}

void TestExtensions::runAtMapping()
{
    QFETCH(QString, runAt);
    QFETCH(int, point);
    const QString dir = makeVariant(m_work.path(), QStringLiteral("runat"), [&](QJsonObject &manifest) {
        QJsonArray scripts = manifest.value(QLatin1String("contentScripts")).toArray();
        QJsonObject script = scripts.first().toObject();
        script.insert(QStringLiteral("runAt"), runAt);
        script.insert(QStringLiteral("allFrames"), true);
        scripts[0] = script;
        manifest.insert(QStringLiteral("contentScripts"), scripts);
    });
    const QString zip = m_work.path() + QStringLiteral("/runat.kondorext");
    QVERIFY(zipDirectory(dir, zip));
    QString error;
    ExtensionManager *manager = ExtensionManager::instance();
    QVERIFY2(manager->installPackage(zip, QStringLiteral("file"), QStringLiteral("sample"), &error),
             qPrintable(error));
    const QList<QWebEngineScript> scripts = manager->scriptsFor(false);
    QCOMPARE(scripts.size(), 1);
    QCOMPARE(int(scripts.first().injectionPoint()), point);
    QVERIFY(scripts.first().runsOnSubFrames());
    QVERIFY(scripts.first().sourceCode().contains(QStringLiteral("// @run-at %1\n").arg(runAt)));
}

void TestExtensions::privateProfileScripts()
{
    QVERIFY(installSample());
    ExtensionManager *manager = ExtensionManager::instance();
    // Off by default in private windows.
    QCOMPARE(manager->scriptsFor(true).size(), 0);
    QCOMPARE(manager->scriptsFor(false).size(), 1);

    manager->applyConfiguration(QStringLiteral("sample"), {}, true, {});
    QCOMPARE(manager->scriptsFor(true).size(), 1);
    QVERIFY(manager->scriptSource(QStringLiteral("sample"), 0, true)
                .contains(QStringLiteral("\"isPrivate\":true")));

    manager->setEnabled(QStringLiteral("sample"), false);
    QCOMPARE(manager->scriptsFor(false).size(), 0);
    QCOMPARE(manager->scriptsFor(true).size(), 0);
}

void TestExtensions::disabledSiteIsInScript()
{
    QVERIFY(installSample());
    ExtensionManager *manager = ExtensionManager::instance();
    const QUrl url(QStringLiteral("https://example.com/page?q=1"));
    QVERIFY(manager->siteEnabled(QStringLiteral("sample"), url));
    manager->setSiteEnabled(QStringLiteral("sample"), url, false);
    QVERIFY(!manager->siteEnabled(QStringLiteral("sample"), url));
    QVERIFY(manager->siteEnabled(QStringLiteral("sample"), QUrl(QStringLiteral("https://other.example/"))));
    QVERIFY(manager->scriptSource(QStringLiteral("sample"), 0, false)
                .contains(QStringLiteral("\"disabledSites\":[\"https://example.com\"]")));
    QCOMPARE(manager->configurationFor(QStringLiteral("sample")).value(QStringLiteral("disabledSites")).toStringList(),
             QStringList{QStringLiteral("https://example.com")});
    manager->setSiteEnabled(QStringLiteral("sample"), url, true);
    QVERIFY(manager->siteEnabled(QStringLiteral("sample"), url));
    // Only web pages have an origin.
    QCOMPARE(ExtensionManager::originOf(QUrl(QStringLiteral("file:///tmp/a.html"))), QString());
    QCOMPARE(ExtensionManager::originOf(QUrl(QStringLiteral("https://Example.com:8443/x"))),
             QStringLiteral("https://example.com:8443"));
}

// --- Install, update, remove ---------------------------------------------------

void TestExtensions::installFromFile()
{
    ExtensionManager *manager = ExtensionManager::instance();
    QSignalSpy pending(manager, &ExtensionManager::pendingInstallChanged);

    manager->inspectFile(samplePackage());
    QCOMPARE(pending.count(), 1);
    const QVariantMap preview = manager->pendingInstall();
    QVERIFY(preview.value(QStringLiteral("valid")).toBool());
    QVERIFY(preview.value(QStringLiteral("fromFile")).toBool());
    QCOMPARE(preview.value(QStringLiteral("name")).toString(), QStringLiteral("Sample Extension"));
    QCOMPARE(preview.value(QStringLiteral("installedVersion")).toString(), QString());
    const QVariantList entries = preview.value(QStringLiteral("permissions")).toList();
    QCOMPARE(entries.size(), 3);
    QCOMPARE(entries.first().toMap().value(QStringLiteral("text")).toString(),
             QStringLiteral("Read and change pages on 127.0.0.1, localhost"));
    // Nothing is installed before the user confirms.
    QVERIFY(!manager->isInstalled(QStringLiteral("sample")));

    manager->confirmInstall();
    QVERIFY(manager->pendingInstall().isEmpty());
    QVERIFY(manager->isInstalled(QStringLiteral("sample")));
    QCOMPARE(manager->source(QStringLiteral("sample")), QStringLiteral("file"));
    QCOMPARE(manager->count(), 1);
    QVERIFY(QFileInfo(ExtensionManager::extensionsDirectory() + QStringLiteral("/sample/manifest.json")).isFile());
    QModelIndex row = manager->index(0);
    QCOMPARE(manager->data(row, ExtensionManager::NameRole).toString(), QStringLiteral("Sample Extension"));
    QVERIFY(manager->data(row, ExtensionManager::EnabledRole).toBool());
    QVERIFY(!manager->data(row, ExtensionManager::PrivateAllowedRole).toBool());
    QVERIFY(manager->data(row, ExtensionManager::HasSettingsRole).toBool());
    QVERIFY(manager->data(row, ExtensionManager::HasActionRole).toBool());

    // A second instance of the manager sees the same install.
    ExtensionManager other;
    QCOMPARE(other.count(), 1);

    // The install dialog asks again for the same id, offering to replace it.
    manager->inspectFile(samplePackage());
    QCOMPARE(manager->pendingInstall().value(QStringLiteral("installedVersion")).toString(),
             QStringLiteral("1.0.0"));
    manager->cancelInstall();
    QVERIFY(manager->pendingInstall().isEmpty());
}

void TestExtensions::invalidFileShowsError()
{
    ExtensionManager *manager = ExtensionManager::instance();
    const QString notZip = m_work.path() + QStringLiteral("/not-a-zip.kondorext");
    QVERIFY(writeFile(notZip, "this is not a zip"));
    manager->inspectFile(notZip);
    QVERIFY(!manager->pendingInstall().value(QStringLiteral("valid")).toBool());
    QVERIFY(!manager->pendingInstall().value(QStringLiteral("error")).toString().isEmpty());
    QCOMPARE(manager->pendingInstall().value(QStringLiteral("fileName")).toString(),
             QStringLiteral("not-a-zip.kondorext"));

    // A valid ZIP without a manifest.
    const QString noManifest = m_work.path() + QStringLiteral("/no-manifest.kondorext");
    {
        KZip zip(noManifest);
        QVERIFY(zip.open(QIODevice::WriteOnly));
        QVERIFY(zip.writeFile(QStringLiteral("content.js"), QByteArray("x")));
        QVERIFY(zip.close());
    }
    manager->inspectFile(noManifest);
    QCOMPARE(manager->pendingInstall().value(QStringLiteral("error")).toString(),
             QStringLiteral("manifest.json: file not found"));
    QCOMPARE(manager->count(), 0);
    // No staging directory is left behind.
    const QStringList leftovers = QDir(ExtensionManager::extensionsDirectory())
                                      .entryList(QDir::Dirs | QDir::NoDotAndDotDot | QDir::Hidden);
    QVERIFY2(leftovers.isEmpty() || (leftovers.size() == 0), qPrintable(leftovers.join(QLatin1Char(','))));
}

void TestExtensions::replaceKeepsState()
{
    QVERIFY(installSample());
    ExtensionManager *manager = ExtensionManager::instance();
    const QString id = QStringLiteral("sample");
    manager->applyConfiguration(id, {{QStringLiteral("greeting"), QStringLiteral("hi")}}, true,
                                {QStringLiteral("https://example.com")});
    manager->setEnabled(id, false);
    QString error;
    QVERIFY2(manager->storageSet(id, QStringLiteral("k"), QJsonValue(1), &error), qPrintable(error));

    const QString dir = makeVariant(m_work.path(), QStringLiteral("v11"), [](QJsonObject &manifest) {
        manifest.insert(QStringLiteral("version"), QStringLiteral("1.1.0"));
    });
    const QString zip = m_work.path() + QStringLiteral("/v11.kondorext");
    QVERIFY(zipDirectory(dir, zip));
    QVERIFY2(manager->installPackage(zip, QStringLiteral("catalog"), id, &error), qPrintable(error));

    QCOMPARE(manager->installedVersion(id), QStringLiteral("1.1.0"));
    QCOMPARE(manager->source(id), QStringLiteral("catalog"));
    QVERIFY(!manager->data(manager->index(0), ExtensionManager::EnabledRole).toBool());
    QVERIFY(manager->data(manager->index(0), ExtensionManager::PrivateAllowedRole).toBool());
    QCOMPARE(manager->settingValues(id).value(QStringLiteral("greeting")).toString(), QStringLiteral("hi"));
    QCOMPARE(manager->storageGet(id, QStringLiteral("k")).toInt(), 1);
    QVERIFY(!QFileInfo::exists(ExtensionManager::extensionsDirectory() + QStringLiteral("/sample.new")));
    QVERIFY(!QFileInfo::exists(ExtensionManager::extensionsDirectory() + QStringLiteral("/sample.old")));

    // A package for another id is refused for an update of this one.
    QVERIFY(!manager->installPackage(samplePackage(), QStringLiteral("catalog"),
                                     QStringLiteral("other"), &error));
    QVERIFY(error.contains(QStringLiteral("not “other”")));
}

void TestExtensions::removeDeletesEverything()
{
    QVERIFY(installSample());
    ExtensionManager *manager = ExtensionManager::instance();
    const QString id = QStringLiteral("sample");
    manager->applyConfiguration(id, {{QStringLiteral("greeting"), QStringLiteral("bye")}}, false, {});
    QString error;
    QVERIFY(manager->storageSet(id, QStringLiteral("k"), QJsonValue(QStringLiteral("v")), &error));

    manager->remove(id);
    QVERIFY(!manager->isInstalled(id));
    QCOMPARE(manager->count(), 0);
    QVERIFY(!QFileInfo::exists(ExtensionManager::extensionsDirectory() + QStringLiteral("/sample")));
    QSettings state(QStringLiteral("KDE"), QStringLiteral("Kondor"));
    state.beginGroup(QStringLiteral("Extensions"));
    QVERIFY(!state.childGroups().contains(id));
    state.endGroup();
    QVERIFY(manager->storageKeys(id).isEmpty());
}

void TestExtensions::settingsAreSanitized()
{
    QVERIFY(installSample());
    ExtensionManager *manager = ExtensionManager::instance();
    const QString id = QStringLiteral("sample");
    QCOMPARE(manager->settingValues(id).value(QStringLiteral("size")).toInt(), 50);

    manager->applyConfiguration(id, {{QStringLiteral("size"), 500},
                                     {QStringLiteral("mode"), QStringLiteral("zzz")},
                                     {QStringLiteral("enabledFeature"), QStringLiteral("nope")},
                                     {QStringLiteral("greeting"), QStringLiteral("changed")}},
                                false, {});
    const QVariantMap values = manager->settingValues(id);
    QCOMPARE(values.value(QStringLiteral("size")).toInt(), 100); // clamped to max
    QCOMPARE(values.value(QStringLiteral("mode")).toString(), QStringLiteral("a")); // not a choice
    QCOMPARE(values.value(QStringLiteral("enabledFeature")).toBool(), true); // not a bool
    QCOMPARE(values.value(QStringLiteral("greeting")).toString(), QStringLiteral("changed"));

    QSignalSpy changed(manager, &ExtensionManager::settingsChanged);
    manager->applyConfiguration(id, {{QStringLiteral("greeting"), QStringLiteral("changed")}}, false, {});
    QCOMPARE(changed.count(), 0); // nothing changed
    manager->applyConfiguration(id, {{QStringLiteral("greeting"), QStringLiteral("again")}}, false, {});
    QCOMPARE(changed.count(), 1);
    QCOMPARE(changed.first().first().toString(), id);
}

// --- Storage and bridge --------------------------------------------------------

void TestExtensions::storageQuota()
{
    QVERIFY(installSample());
    ExtensionManager *manager = ExtensionManager::instance();
    const QString id = QStringLiteral("sample");
    QString error;
    QVERIFY(manager->storageSet(id, QStringLiteral("a"), QJsonValue(QString(600 * 1024, QLatin1Char('x'))), &error));
    // 600 KiB + 600 KiB is over the 1 MiB of one extension.
    QVERIFY(!manager->storageSet(id, QStringLiteral("b"), QJsonValue(QString(600 * 1024, QLatin1Char('y'))), &error));
    QVERIFY(error.contains(QLatin1String("full")));
    QVERIFY(!manager->storageKeys(id).contains(QStringLiteral("b")));
    // Replacing a value counts only the new size.
    QVERIFY(manager->storageSet(id, QStringLiteral("a"), QJsonValue(QString(900 * 1024, QLatin1Char('z'))), &error));
    // Structured values round-trip.
    manager->storageRemove(id, QStringLiteral("a"));
    const QJsonObject object{{QStringLiteral("n"), 1}, {QStringLiteral("list"), QJsonArray{1, 2}}};
    QVERIFY(manager->storageSet(id, QStringLiteral("obj"), object, &error));
    QCOMPARE(manager->storageGet(id, QStringLiteral("obj")).toObject(), object);
    QVERIFY(manager->storageGet(id, QStringLiteral("missing")).isNull());
}

void TestExtensions::storageIsPerExtension()
{
    QVERIFY(installSample());
    ExtensionManager *manager = ExtensionManager::instance();
    QString error;
    QVERIFY(manager->storageSet(QStringLiteral("sample"), QStringLiteral("k"), QJsonValue(1), &error));
    QVERIFY(manager->storageGet(QStringLiteral("other"), QStringLiteral("k")).isNull());
    QCOMPARE(manager->storageKeys(QStringLiteral("sample")), QStringList{QStringLiteral("k")});
    QVERIFY(manager->storageKeys(QStringLiteral("other")).isEmpty());
}

namespace {
QString token(const QString &id)
{
    // The token lives in the generated script; the bridge tests read it from there.
    const QString source = ExtensionManager::instance()->scriptSource(id, 0, true);
    const QString marker = QStringLiteral("\"token\":\"");
    const int start = source.indexOf(marker);
    if (start < 0)
        return QString();
    const int from = start + marker.size();
    return source.mid(from, source.indexOf(QLatin1Char('"'), from) - from);
}

QJsonObject call(ExtensionBridge &bridge, const QString &id, const QString &token, const QString &method,
                 const QJsonArray &args = {})
{
    return QJsonDocument::fromJson(
               bridge.request(id, token, method,
                              QString::fromUtf8(QJsonDocument(args).toJson(QJsonDocument::Compact))).toUtf8())
        .object();
}
} // namespace

void TestExtensions::bridgeRejectsWrongToken()
{
    QVERIFY(installSample());
    ExtensionManager *manager = ExtensionManager::instance();
    manager->applyConfiguration(QStringLiteral("sample"), {}, true, {});
    Tab tab(nullptr);
    ExtensionBridge bridge;
    bridge.setTab(&tab);

    const QString good = token(QStringLiteral("sample"));
    QVERIFY(!good.isEmpty());
    QVERIFY(call(bridge, QStringLiteral("sample"), good, QStringLiteral("storage.keys")).value(QStringLiteral("ok")).toBool());

    const QJsonObject wrong = call(bridge, QStringLiteral("sample"), QStringLiteral("wrong"), QStringLiteral("storage.keys"));
    QVERIFY(!wrong.value(QStringLiteral("ok")).toBool());
    QCOMPARE(wrong.value(QStringLiteral("error")).toString(), QStringLiteral("Invalid extension token"));
    QVERIFY(!call(bridge, QStringLiteral("sample"), QString(), QStringLiteral("storage.keys")).value(QStringLiteral("ok")).toBool());
    // Another extension's id with this token, and an unknown id.
    QVERIFY(!call(bridge, QStringLiteral("other"), good, QStringLiteral("storage.keys")).value(QStringLiteral("ok")).toBool());
    // A bridge without a tab answers nothing.
    ExtensionBridge orphan;
    QVERIFY(!call(orphan, QStringLiteral("sample"), good, QStringLiteral("storage.keys")).value(QStringLiteral("ok")).toBool());
}

void TestExtensions::bridgeEnforcesPermissions()
{
    // The sample asks for "tabs" and "notifications", not "downloads".
    QVERIFY(installSample());
    Tab tab(nullptr);
    ExtensionBridge bridge;
    bridge.setTab(&tab);
    const QString good = token(QStringLiteral("sample"));
    ExtensionManager::instance()->applyConfiguration(QStringLiteral("sample"), {}, true, {});

    const QJsonObject download = call(bridge, QStringLiteral("sample"), good, QStringLiteral("download"),
                                      {QStringLiteral("https://example.com/f.zip"), QString()});
    QVERIFY(!download.value(QStringLiteral("ok")).toBool());
    QVERIFY(download.value(QStringLiteral("error")).toString().contains(QLatin1String("\"downloads\"")));

    // A variant without "tabs" cannot use tabs.*.
    const QString dir = makeVariant(m_work.path(), QStringLiteral("notabs"), [](QJsonObject &manifest) {
        manifest.insert(QStringLiteral("permissions"), QJsonArray());
    });
    const QString zip = m_work.path() + QStringLiteral("/notabs.kondorext");
    QVERIFY(zipDirectory(dir, zip));
    QString error;
    QVERIFY2(ExtensionManager::instance()->installPackage(zip, QStringLiteral("file"), QStringLiteral("sample"), &error),
             qPrintable(error));
    ExtensionManager::instance()->applyConfiguration(QStringLiteral("sample"), {}, true, {});
    const QString token2 = token(QStringLiteral("sample"));
    QVERIFY(token2 != good); // a new package, a new token
    QSignalSpy closes(&tab, &Tab::closeRequested);
    const QJsonObject close = call(bridge, QStringLiteral("sample"), token2, QStringLiteral("tabs.close"));
    QVERIFY(!close.value(QStringLiteral("ok")).toBool());
    QVERIFY(close.value(QStringLiteral("error")).toString().contains(QLatin1String("\"tabs\"")));
    QCOMPARE(closes.count(), 0);
    QVERIFY(!call(bridge, QStringLiteral("sample"), token2, QStringLiteral("notify"),
                  {QStringLiteral("t"), QStringLiteral("b")}).value(QStringLiteral("ok")).toBool());
}

void TestExtensions::bridgeStorageReadOnlyInPrivate()
{
    QVERIFY(installSample());
    ExtensionManager *manager = ExtensionManager::instance();
    manager->applyConfiguration(QStringLiteral("sample"), {}, true, {}); // allowed in private windows
    QQuickWebEngineProfile privateProfile;
    QVERIFY(privateProfile.isOffTheRecord());
    Tab privateTab(&privateProfile);
    QVERIFY(privateTab.isPrivate());
    Tab normalTab(nullptr);
    ExtensionBridge privateBridge;
    privateBridge.setTab(&privateTab);
    ExtensionBridge normalBridge;
    normalBridge.setTab(&normalTab);
    const QString good = token(QStringLiteral("sample"));

    QVERIFY(call(normalBridge, QStringLiteral("sample"), good, QStringLiteral("storage.set"),
                 {QStringLiteral("k"), 42}).value(QStringLiteral("ok")).toBool());
    const QJsonObject read = call(privateBridge, QStringLiteral("sample"), good, QStringLiteral("storage.get"),
                                  {QStringLiteral("k")});
    QVERIFY(read.value(QStringLiteral("ok")).toBool());
    QCOMPARE(read.value(QStringLiteral("value")).toInt(), 42);

    const QJsonObject write = call(privateBridge, QStringLiteral("sample"), good, QStringLiteral("storage.set"),
                                   {QStringLiteral("k"), 1});
    QVERIFY(!write.value(QStringLiteral("ok")).toBool());
    QCOMPARE(write.value(QStringLiteral("error")).toString(),
             QStringLiteral("Storage is read-only in private windows"));
    QVERIFY(!call(privateBridge, QStringLiteral("sample"), good, QStringLiteral("storage.remove"),
                  {QStringLiteral("k")}).value(QStringLiteral("ok")).toBool());
    QCOMPARE(manager->storageGet(QStringLiteral("sample"), QStringLiteral("k")).toInt(), 42);

    // Not allowed in private windows: the bridge refuses everything there.
    manager->applyConfiguration(QStringLiteral("sample"), {}, false, {});
    QVERIFY(!call(privateBridge, QStringLiteral("sample"), good, QStringLiteral("storage.get"),
                  {QStringLiteral("k")}).value(QStringLiteral("ok")).toBool());
    QVERIFY(call(normalBridge, QStringLiteral("sample"), good, QStringLiteral("storage.get"),
                 {QStringLiteral("k")}).value(QStringLiteral("ok")).toBool());
}

void TestExtensions::bridgeTabCommands()
{
    QVERIFY(installSample());
    ExtensionManager::instance()->applyConfiguration(QStringLiteral("sample"), {}, true, {});
    Tab tab(nullptr);
    ExtensionBridge bridge;
    bridge.setTab(&tab);
    const QString good = token(QStringLiteral("sample"));
    const QString id = QStringLiteral("sample");

    QSignalSpy closes(&tab, &Tab::closeRequested);
    QSignalSpy opens(&tab, &Tab::openTabRequested);
    QSignalSpy neighbors(&tab, &Tab::neighborTabRequested);
    QSignalSpy reloads(&tab, &Tab::reloadRequested);

    QVERIFY(call(bridge, id, good, QStringLiteral("tabs.close")).value(QStringLiteral("ok")).toBool());
    QCOMPARE(closes.count(), 1);
    QVERIFY(call(bridge, id, good, QStringLiteral("tabs.reload")).value(QStringLiteral("ok")).toBool());
    QCOMPARE(reloads.count(), 1);
    QVERIFY(call(bridge, id, good, QStringLiteral("tabs.next")).value(QStringLiteral("ok")).toBool());
    QVERIFY(call(bridge, id, good, QStringLiteral("tabs.previous")).value(QStringLiteral("ok")).toBool());
    QCOMPARE(neighbors.count(), 2);
    QCOMPARE(neighbors.at(0).at(0).toInt(), 1);
    QCOMPARE(neighbors.at(1).at(0).toInt(), -1);

    QVERIFY(call(bridge, id, good, QStringLiteral("tabs.open"),
                 {QStringLiteral("https://example.com/"), true}).value(QStringLiteral("ok")).toBool());
    QCOMPARE(opens.count(), 1);
    QCOMPARE(opens.first().at(0).toUrl(), QUrl(QStringLiteral("https://example.com/")));
    QVERIFY(opens.first().at(1).toBool());
    // Only web addresses.
    QVERIFY(!call(bridge, id, good, QStringLiteral("tabs.open"),
                  {QStringLiteral("file:///etc/passwd"), false}).value(QStringLiteral("ok")).toBool());
    QVERIFY(!call(bridge, id, good, QStringLiteral("tabs.open"),
                  {QStringLiteral("javascript:alert(1)"), false}).value(QStringLiteral("ok")).toBool());
    QCOMPARE(opens.count(), 1);

    QVERIFY(!call(bridge, id, good, QStringLiteral("no.such.method")).value(QStringLiteral("ok")).toBool());

    // Toolbar items: the checked state is per tab.
    QVERIFY(call(bridge, id, good, QStringLiteral("action.setChecked"),
                 {QStringLiteral("toggle"), true}).value(QStringLiteral("ok")).toBool());
    QVERIFY(tab.extensionItemChecked(id, QStringLiteral("toggle")));
    Tab other(nullptr);
    QVERIFY(!other.extensionItemChecked(id, QStringLiteral("toggle")));
    QSignalSpy triggered(&tab, &Tab::extensionItemTriggered);
    tab.triggerExtensionItem(id, QStringLiteral("toggle"), true);
    QVERIFY(!tab.extensionItemChecked(id, QStringLiteral("toggle")));
    QCOMPARE(triggered.count(), 1);
    QVERIFY(!triggered.first().at(2).toBool());
}

void TestExtensions::bridgeOffExtension()
{
    QVERIFY(installSample());
    ExtensionManager *manager = ExtensionManager::instance();
    Tab tab(nullptr);
    ExtensionBridge bridge;
    bridge.setTab(&tab);
    const QString good = token(QStringLiteral("sample"));
    manager->applyConfiguration(QStringLiteral("sample"), {}, true, {});
    manager->setEnabled(QStringLiteral("sample"), false);
    QVERIFY(!call(bridge, QStringLiteral("sample"), good, QStringLiteral("storage.keys")).value(QStringLiteral("ok")).toBool());
}

// --- Updates and catalog -------------------------------------------------------

void TestExtensions::silentUpdateRule()
{
    const QStringList matches{QStringLiteral("https://a.com/*"), QStringLiteral("https://b.com/*")};
    const QStringList permissions{QStringLiteral("tabs")};
    using C = ExtensionCatalog;
    QVERIFY(C::isSilentUpdate(matches, permissions, matches, permissions));
    // A subset is fine.
    QVERIFY(C::isSilentUpdate({QStringLiteral("https://a.com/*")}, {}, matches, permissions));
    QVERIFY(C::isSilentUpdate({}, {}, matches, permissions));
    // A new site or a new permission asks again.
    QVERIFY(!C::isSilentUpdate({QStringLiteral("https://c.com/*")}, permissions, matches, permissions));
    QVERIFY(!C::isSilentUpdate(matches, {QStringLiteral("tabs"), QStringLiteral("downloads")}, matches, permissions));
    QVERIFY(!C::isSilentUpdate({QStringLiteral("<all_urls>")}, permissions, matches, permissions));
}

namespace {
// Writes a catalog with one "sample" entry (a copy of the sample with this
// version and permissions) under `root` and returns the catalog file's URL.
QUrl writeCatalog(const QString &root, const QString &version, const QStringList &permissions,
                  const QString &shaOverride = QString(), qint64 sizeOverride = -1,
                  const QStringList &catalogPermissions = QStringList(), bool overrideCatalogPermissions = false)
{
    const QString dir = makeVariant(root, QStringLiteral("pkg-") + version, [&](QJsonObject &manifest) {
        manifest.insert(QStringLiteral("version"), version);
        manifest.insert(QStringLiteral("permissions"), QJsonArray::fromStringList(permissions));
    });
    const QString zip = root + QStringLiteral("/packages/sample-%1.kondorext").arg(version);
    QDir().mkpath(root + QStringLiteral("/packages"));
    zipDirectory(dir, zip);
    const QJsonObject entry{
        {QStringLiteral("id"), QStringLiteral("sample")},
        {QStringLiteral("name"), QStringLiteral("Sample Extension")},
        {QStringLiteral("name[pt_BR]"), QStringLiteral("Extensão de Exemplo")},
        {QStringLiteral("description"), QStringLiteral("Marks pages.")},
        {QStringLiteral("version"), version},
        {QStringLiteral("author"), QStringLiteral("Kondor contributors")},
        {QStringLiteral("icon"), QStringLiteral("weather-clear-night")},
        {QStringLiteral("permissions"), QJsonArray::fromStringList(overrideCatalogPermissions ? catalogPermissions : permissions)},
        {QStringLiteral("matches"), QJsonArray{QStringLiteral("*://127.0.0.1/*"), QStringLiteral("*://localhost/*")}},
        {QStringLiteral("package"), QStringLiteral("packages/sample-%1.kondorext").arg(version)},
        {QStringLiteral("sha256"), shaOverride.isEmpty() ? sha256Of(zip) : shaOverride},
        {QStringLiteral("size"), sizeOverride >= 0 ? sizeOverride : QFileInfo(zip).size()},
    };
    const QJsonObject catalog{{QStringLiteral("version"), 1},
                              {QStringLiteral("generated"), QStringLiteral("2026-11-10T21:00:00Z")},
                              {QStringLiteral("extensions"), QJsonArray{entry}}};
    const QString file = root + QStringLiteral("/catalog.json");
    writeFile(file, QJsonDocument(catalog).toJson());
    return QUrl::fromLocalFile(file);
}

bool refreshCatalog(ExtensionCatalog *catalog, const QUrl &url)
{
    catalog->setCatalogUrl(url);
    QSignalSpy states(catalog, &ExtensionCatalog::stateChanged);
    catalog->refresh();
    return QTest::qWaitFor([&]() { return catalog->state() == QLatin1String("ready")
                                          || catalog->state() == QLatin1String("error"); }, 10000)
        && catalog->state() == QLatin1String("ready");
}
} // namespace

void TestExtensions::catalogLoadsAndInstalls()
{
    QTemporaryDir root;
    const QUrl url = writeCatalog(root.path(), QStringLiteral("1.0.0"), {QStringLiteral("tabs")});
    ExtensionCatalog *catalog = ExtensionCatalog::instance();
    QVERIFY(refreshCatalog(catalog, url));
    QCOMPARE(catalog->rowCount(), 1);
    const QModelIndex row = catalog->index(0);
    QCOMPARE(catalog->data(row, ExtensionCatalog::IdRole).toString(), QStringLiteral("sample"));
    QCOMPARE(catalog->data(row, ExtensionCatalog::NameRole).toString().isEmpty(), false);
    QCOMPARE(catalog->data(row, ExtensionCatalog::IconSourceRole).toString(), QStringLiteral("weather-clear-night"));
    QVERIFY(!catalog->data(row, ExtensionCatalog::InstalledRole).toBool());
    QVERIFY(QFileInfo(ExtensionCatalog::cacheFile()).isFile());

    // Install: download, check, then the confirmation (not from a file).
    catalog->install(QStringLiteral("sample"));
    ExtensionManager *manager = ExtensionManager::instance();
    QVERIFY(QTest::qWaitFor([&]() { return !manager->pendingInstall().isEmpty(); }, 10000));
    QVERIFY(manager->pendingInstall().value(QStringLiteral("valid")).toBool());
    QVERIFY(!manager->pendingInstall().value(QStringLiteral("fromFile")).toBool());
    QVERIFY(!manager->isInstalled(QStringLiteral("sample")));
    manager->confirmInstall();
    QVERIFY(manager->isInstalled(QStringLiteral("sample")));
    QCOMPARE(manager->source(QStringLiteral("sample")), QStringLiteral("catalog"));
    QVERIFY(catalog->data(row, ExtensionCatalog::InstalledRole).toBool());
    QVERIFY(catalog->installError().isEmpty());
}

void TestExtensions::catalogRejectsBadChecksum()
{
    QTemporaryDir root;
    const QUrl url = writeCatalog(root.path(), QStringLiteral("1.0.0"), {QStringLiteral("tabs")},
                                  QString(64, QLatin1Char('0')));
    ExtensionCatalog *catalog = ExtensionCatalog::instance();
    QVERIFY(refreshCatalog(catalog, url));
    catalog->install(QStringLiteral("sample"));
    QVERIFY(QTest::qWaitFor([&]() { return !catalog->installError().isEmpty(); }, 10000));
    QVERIFY2(catalog->installError().contains(QLatin1String("checksum")), qPrintable(catalog->installError()));
    QVERIFY(ExtensionManager::instance()->pendingInstall().isEmpty());
    QVERIFY(!ExtensionManager::instance()->isInstalled(QStringLiteral("sample")));
    QVERIFY(catalog->installingId().isEmpty());
}

void TestExtensions::catalogRejectsOversizedPackage()
{
    QTemporaryDir root;
    // The catalog promises fewer bytes than the file has.
    const QUrl url = writeCatalog(root.path(), QStringLiteral("1.0.0"), {QStringLiteral("tabs")},
                                  QString(), 10);
    ExtensionCatalog *catalog = ExtensionCatalog::instance();
    QVERIFY(refreshCatalog(catalog, url));
    catalog->install(QStringLiteral("sample"));
    QVERIFY(QTest::qWaitFor([&]() { return !catalog->installError().isEmpty(); }, 10000));
    QVERIFY(ExtensionManager::instance()->pendingInstall().isEmpty());
    QVERIFY(!ExtensionManager::instance()->isInstalled(QStringLiteral("sample")));
}

void TestExtensions::catalogUpdates()
{
    ExtensionManager *manager = ExtensionManager::instance();
    ExtensionCatalog *catalog = ExtensionCatalog::instance();
    Settings::instance()->setExtensionsAutoUpdate(true);

    QTemporaryDir root;
    QUrl url = writeCatalog(root.path(), QStringLiteral("1.0.0"), {QStringLiteral("tabs")});
    QVERIFY(refreshCatalog(catalog, url));
    catalog->install(QStringLiteral("sample"));
    QVERIFY(QTest::qWaitFor([&]() { return !manager->pendingInstall().isEmpty(); }, 10000));
    manager->confirmInstall();
    QCOMPARE(manager->installedVersion(QStringLiteral("sample")), QStringLiteral("1.0.0"));

    // A newer version without new permissions installs by itself.
    url = writeCatalog(root.path(), QStringLiteral("1.1.0"), {QStringLiteral("tabs")});
    QVERIFY(refreshCatalog(catalog, url));
    QVERIFY(QTest::qWaitFor([&]() { return manager->installedVersion(QStringLiteral("sample")) == QLatin1String("1.1.0"); }, 10000));
    QVERIFY(manager->pendingInstall().isEmpty());
    QVERIFY(!manager->data(manager->index(0), ExtensionManager::UpdateAvailableRole).toBool());

    // A new permission only marks it for review.
    url = writeCatalog(root.path(), QStringLiteral("1.2.0"), {QStringLiteral("tabs"), QStringLiteral("downloads")});
    QVERIFY(refreshCatalog(catalog, url));
    QVERIFY(QTest::qWaitFor([&]() { return manager->data(manager->index(0), ExtensionManager::UpdateNeedsReviewRole).toBool(); }, 10000));
    QCOMPARE(manager->installedVersion(QStringLiteral("sample")), QStringLiteral("1.1.0"));
    QVERIFY(catalog->data(catalog->index(0), ExtensionCatalog::UpdateAvailableRole).toBool());

    // The catalog claims the old permissions but the package adds one: not silent.
    url = writeCatalog(root.path(), QStringLiteral("1.1.5"), {QStringLiteral("tabs"), QStringLiteral("downloads")},
                       QString(), -1, {QStringLiteral("tabs")}, true);
    QVERIFY(refreshCatalog(catalog, url));
    QVERIFY(QTest::qWaitFor([&]() { return manager->data(manager->index(0), ExtensionManager::UpdateNeedsReviewRole).toBool(); }, 10000));
    QCOMPARE(manager->installedVersion(QStringLiteral("sample")), QStringLiteral("1.1.0"));
    QVERIFY(!manager->installedPermissions(QStringLiteral("sample")).contains(QLatin1String("downloads")));

    // A new permission only marks it for review.
    url = writeCatalog(root.path(), QStringLiteral("1.2.0"), {QStringLiteral("tabs"), QStringLiteral("downloads")});
    QVERIFY(refreshCatalog(catalog, url));
    QTest::qWait(300);
    QCOMPARE(manager->installedVersion(QStringLiteral("sample")), QStringLiteral("1.1.0"));

    // "Update…" asks first, with the replacement text.
    catalog->install(QStringLiteral("sample"));
    QVERIFY(QTest::qWaitFor([&]() { return !manager->pendingInstall().isEmpty(); }, 10000));
    QCOMPARE(manager->pendingInstall().value(QStringLiteral("installedVersion")).toString(), QStringLiteral("1.1.0"));
    QCOMPARE(manager->pendingInstall().value(QStringLiteral("version")).toString(), QStringLiteral("1.2.0"));
    manager->confirmInstall();
    QCOMPARE(manager->installedVersion(QStringLiteral("sample")), QStringLiteral("1.2.0"));

    // With automatic updates off, nothing is installed on its own.
    Settings::instance()->setExtensionsAutoUpdate(false);
    url = writeCatalog(root.path(), QStringLiteral("1.3.0"), {QStringLiteral("tabs"), QStringLiteral("downloads")});
    QVERIFY(refreshCatalog(catalog, url));
    QTest::qWait(300);
    QCOMPARE(manager->installedVersion(QStringLiteral("sample")), QStringLiteral("1.2.0"));
    Settings::instance()->setExtensionsAutoUpdate(true);

    // File installs are never updated automatically.
    QVERIFY(installSample(QStringLiteral("file")));
    QCOMPARE(manager->installedVersion(QStringLiteral("sample")), QStringLiteral("1.0.0"));
    QVERIFY(refreshCatalog(catalog, url));
    QTest::qWait(300);
    QCOMPARE(manager->installedVersion(QStringLiteral("sample")), QStringLiteral("1.0.0"));
}

// --- The QML of the toolbar menu and the dialogs -------------------------------

namespace {
QObject *createInWindow(QQmlEngine *engine, const QByteArray &source, const QVariantMap &properties = {})
{
    engine->addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));
    QQmlComponent component(engine);
    component.setData(source, QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR "/Host.qml")));
    QObject *object = component.createWithInitialProperties(properties);
    if (!object)
        qWarning() << component.errors();
    return object;
}
}

void TestExtensions::toolbarMenuEntries()
{
    QVERIFY(installSample());
    ExtensionManager *manager = ExtensionManager::instance();
    Tab tab(nullptr);
    tab.setUrl(QUrl(QStringLiteral("https://www.example.com/page")));
    tab.setExtensionItemChecked(QStringLiteral("sample"), QStringLiteral("toggle"), true);

    // The menu needs the tab as a context property of its host.
    m_engine.rootContext()->setContextProperty(QStringLiteral("theTab"), &tab);
    QObject *window = createInWindow(&m_engine,
        "import QtQuick\nimport QtQuick.Controls\nimport Kondor\n"
        "ApplicationWindow {\n"
        "    property alias menu: menu\n"
        "    ExtensionsMenu { id: menu; tab: theTab }\n"
        "}\n");
    QVERIFY(window);
    QObject *menu = window->property("menu").value<QObject *>();
    QVERIFY(menu);
    QMetaObject::invokeMethod(menu, "rebuild");
    const QVariantList entries = menu->property("entries").toList();
    // Header, the toggle item, then "Run on <site>".
    QCOMPARE(entries.size(), 3);
    QCOMPARE(entries.at(0).toMap().value(QStringLiteral("kind")).toString(), QStringLiteral("header"));
    QCOMPARE(entries.at(0).toMap().value(QStringLiteral("title")).toString(), QStringLiteral("Sample Extension"));
    QCOMPARE(entries.at(1).toMap().value(QStringLiteral("title")).toString(), QStringLiteral("Toggle Mark"));
    QVERIFY(entries.at(1).toMap().value(QStringLiteral("checked")).toBool()); // per tab
    QCOMPARE(entries.at(2).toMap().value(QStringLiteral("title")).toString(),
             QStringLiteral("Run on www.example.com"));
    QVERIFY(entries.at(2).toMap().value(QStringLiteral("checked")).toBool());

    // A site the extension is turned off on shows unchecked.
    manager->setSiteEnabled(QStringLiteral("sample"), tab.url(), false);
    QMetaObject::invokeMethod(menu, "rebuild");
    QVERIFY(!menu->property("entries").toList().at(2).toMap().value(QStringLiteral("checked")).toBool());

    // Private tab: only extensions allowed there, and no site toggle.
    QQuickWebEngineProfile privateProfile;
    Tab privateTab(&privateProfile);
    privateTab.setUrl(QUrl(QStringLiteral("https://www.example.com/page")));
    m_engine.rootContext()->setContextProperty(QStringLiteral("theTab"), &privateTab);
    menu->setProperty("tab", QVariant::fromValue(&privateTab));
    QMetaObject::invokeMethod(menu, "rebuild");
    QCOMPARE(menu->property("entries").toList().size(), 0);
    manager->applyConfiguration(QStringLiteral("sample"), {}, true, {});
    QMetaObject::invokeMethod(menu, "rebuild");
    const QVariantList privateEntries = menu->property("entries").toList();
    QCOMPARE(privateEntries.size(), 2); // header + toggle, no "Run on"
    delete window;
    m_engine.rootContext()->setContextProperty(QStringLiteral("theTab"), nullptr);
}

void TestExtensions::configureDialogWritesValues()
{
    QVERIFY(installSample());
    ExtensionManager *manager = ExtensionManager::instance();
    QObject *window = createInWindow(&m_engine,
        "import QtQuick\nimport QtQuick.Controls\nimport Kondor\n"
        "ApplicationWindow {\n"
        "    property alias dialog: dialog\n"
        "    ExtensionSettingsDialog { id: dialog }\n"
        "}\n");
    QVERIFY(window);
    QObject *dialog = window->property("dialog").value<QObject *>();
    QMetaObject::invokeMethod(dialog, "openFor", Q_ARG(QVariant, QStringLiteral("sample")));
    QCOMPARE(dialog->property("values").toMap().value(QStringLiteral("greeting")).toString(), QStringLiteral("hello"));
    QCOMPARE(dialog->property("schema").toList().size(), 4);

    QMetaObject::invokeMethod(dialog, "setValue", Q_ARG(QVariant, QStringLiteral("greeting")),
                              Q_ARG(QVariant, QStringLiteral("ola")));
    dialog->setProperty("privateAllowed", true);
    // Nothing is written before OK.
    QCOMPARE(manager->settingValues(QStringLiteral("sample")).value(QStringLiteral("greeting")).toString(),
             QStringLiteral("hello"));
    QMetaObject::invokeMethod(dialog, "accept");
    QCOMPARE(manager->settingValues(QStringLiteral("sample")).value(QStringLiteral("greeting")).toString(),
             QStringLiteral("ola"));
    QVERIFY(manager->data(manager->index(0), ExtensionManager::PrivateAllowedRole).toBool());

    // Restore Defaults puts the manifest defaults back in the form (still pending).
    QMetaObject::invokeMethod(dialog, "openFor", Q_ARG(QVariant, QStringLiteral("sample")));
    QMetaObject::invokeMethod(dialog, "restoreDefaults");
    QCOMPARE(dialog->property("values").toMap().value(QStringLiteral("greeting")).toString(), QStringLiteral("hello"));
    QCOMPARE(manager->settingValues(QStringLiteral("sample")).value(QStringLiteral("greeting")).toString(),
             QStringLiteral("ola"));
    delete window;
}

void TestExtensions::installDialogShowsPendingInstall()
{
    ExtensionManager *manager = ExtensionManager::instance();
    QObject *window = createInWindow(&m_engine,
        "import QtQuick\nimport QtQuick.Controls\nimport Kondor\n"
        "ApplicationWindow {\n"
        "    visible: true\n"
        "    property alias dialog: dialog\n"
        "    InstallExtensionDialog { id: dialog; parent: Overlay.overlay }\n"
        "}\n");
    QVERIFY(window);
    QObject *dialog = window->property("dialog").value<QObject *>();
    QVERIFY(!dialog->property("visible").toBool());

    manager->inspectFile(samplePackage());
    QVERIFY(dialog->property("isValid").toBool());
    QTRY_VERIFY(dialog->property("visible").toBool());
    QVERIFY(!dialog->property("replacing").toBool());

    // Closing the dialog drops the pending install.
    QMetaObject::invokeMethod(dialog, "close");
    QTRY_VERIFY(manager->pendingInstall().isEmpty());

    // A file that is not an extension shows only the error.
    const QString notZip = m_work.path() + QStringLiteral("/bad.kondorext");
    QVERIFY(writeFile(notZip, "nope"));
    manager->inspectFile(notZip);
    QVERIFY(!dialog->property("isValid").toBool());
    QVERIFY(dialog->property("hasInfo").toBool());
    QTRY_VERIFY(dialog->property("visible").toBool());
    manager->cancelInstall();
    delete window;
}

void TestExtensions::extensionsPageListsInstalled()
{
    QObject *window = createInWindow(&m_engine,
        "import QtQuick\nimport QtQuick.Controls\nimport Kondor\n"
        "ApplicationWindow {\n"
        "    visible: true\n"
        "    width: 700; height: 400\n"
        "    ExtensionsPage { anchors.fill: parent }\n"
        "}\n");
    QVERIFY(window);
    QQuickItem *list = window->findChild<QQuickItem *>(QStringLiteral("extensionList"));
    QVERIFY(list);
    QCOMPARE(list->property("count").toInt(), 0);
    QVERIFY(installSample());
    QTRY_COMPARE(list->property("count").toInt(), 1);
    // The row (an ItemDelegate) stays enabled when the extension is turned off.
    ExtensionManager::instance()->setEnabled(QStringLiteral("sample"), false);
    QQuickItem *row = nullptr;
    QTRY_VERIFY2((QMetaObject::invokeMethod(list, "itemAtIndex", Q_RETURN_ARG(QQuickItem *, row),
                                            Q_ARG(int, 0)), row), "the row was not created");
    QVERIFY(row->isEnabled());
    delete window;
}

// --- A real page ---------------------------------------------------------------

void TestExtensions::contentScriptRunsInPages()
{
    PageServer server;
    QVERIFY(server.port() > 0);
    server.start();

    ExtensionManager *manager = ExtensionManager::instance();
    ProfileManager *profiles = ProfileManager::instance();
    QObject::connect(profiles, &ProfileManager::profileCreated, manager, &ExtensionManager::registerProfile);
    QQuickWebEngineProfile *normalProfile = profiles->defaultProfile();
    QQuickWebEngineProfile *privateProfile = profiles->createPrivateProfile();
    manager->registerProfile(normalProfile);
    // The default profile was created above, before the connection could fire.
    QVERIFY(installSample());

    QQuickWindow window;
    window.resize(400, 300);
    window.show();

    const QByteArray qml =
        "import QtQuick\nimport QtWebEngine\nimport QtWebChannel\n"
        "WebEngineView {\n"
        "    id: view\n"
        "    property var result\n"
        "    property bool done: false\n"
        "    property alias pageChannel: channel\n"
        "    property bool loaded: false\n"
        "    onLoadingChanged: function(info) {\n"
        "        if (info.status === WebEngineLoadingInfo.LoadSucceededStatus) loaded = true\n"
        "    }\n"
        "    function load(address) { loaded = false; url = address }\n"
        "    width: 400; height: 300\n"
        "    webChannel: channel\n"
        "    webChannelWorld: WebEngineScript.ApplicationWorld\n"
        "    WebChannel { id: channel }\n"
        "    function run(code) {\n"
        "        done = false; result = undefined\n"
        "        runJavaScript(code, WebEngineScript.MainWorld, function(r) { result = r; done = true })\n"
        "    }\n"
        "}\n";

    struct Page {
        QQuickItem *view = nullptr;
        Tab *tab = nullptr;
        ExtensionBridge *bridge = nullptr;
    };
    const auto openPage = [&](QQuickWebEngineProfile *profile, const QUrl &url) {
        Page page;
        QQmlComponent component(&m_engine);
        component.setData(qml, QUrl());
        page.view = qobject_cast<QQuickItem *>(component.createWithInitialProperties(
            {{QStringLiteral("profile"), QVariant::fromValue(profile)}}));
        if (!page.view) {
            qWarning() << component.errors();
            return page;
        }
        page.view->setParentItem(window.contentItem());
        page.tab = new Tab(profile, page.view);
        page.bridge = new ExtensionBridge(page.view);
        page.bridge->setTab(page.tab);
        QObject *channel = page.view->property("pageChannel").value<QObject *>();
        QMetaObject::invokeMethod(channel, "registerObject", Q_ARG(QString, QStringLiteral("kondorExtensions")),
                                  Q_ARG(QObject *, page.bridge->pageApi()));
        QMetaObject::invokeMethod(page.view, "load", Q_ARG(QVariant, url));
        return page;
    };
    const auto evaluate = [](const Page &page, const QString &code) {
        QMetaObject::invokeMethod(page.view, "run", Q_ARG(QVariant, code));

        (void)QTest::qWaitFor([&]() { return page.view->property("done").toBool(); }, 5000);
        return page.view->property("result");
    };
    const auto waitLoaded = [](const Page &page) {
        return QTest::qWaitFor([&]() { return page.view->property("loaded").toBool(); }, 30000);
    };
    const auto attribute = [&](const Page &page, const QString &name) {
        return evaluate(page, QStringLiteral("document.readyState === 'complete' ? "
                                             "document.documentElement.getAttribute('%1') : 'loading'").arg(name));
    };

    // Normal profile: the script runs, with its settings and storage.
    Page normal = openPage(normalProfile, server.url());
    QVERIFY(normal.view);
    QVERIFY(waitLoaded(normal));
    QTRY_COMPARE_WITH_TIMEOUT(attribute(normal, QStringLiteral("data-kondor-sample")).toString(),
                              QStringLiteral("hello"), 10000);
    QCOMPARE(attribute(normal, QStringLiteral("data-kondor-private")).toString(), QStringLiteral("false"));
    QTRY_COMPARE_WITH_TIMEOUT(attribute(normal, QStringLiteral("data-kondor-storage")).toString(),
                              QStringLiteral("ok"), 10000);
    QCOMPARE(manager->storageGet(QStringLiteral("sample"), QStringLiteral("lastGreeting")).toString(),
             QStringLiteral("hello"));

    // A setting change reaches the open page (WebViewTab.qml does the same).
    manager->applyConfiguration(QStringLiteral("sample"), {{QStringLiteral("greeting"), QStringLiteral("hola")}}, false, {});
    QMetaObject::invokeMethod(normal.view, "runJavaScript",
                              Q_ARG(QString, QStringLiteral("window.__kondorExtensions['sample'](%1);")
                                                 .arg(QString::fromUtf8(QJsonDocument(QJsonObject::fromVariantMap(
                                                     manager->settingValues(QStringLiteral("sample"))))
                                                                            .toJson(QJsonDocument::Compact)))),
                              Q_ARG(uint, uint(QWebEngineScript::ApplicationWorld)));
    QTRY_COMPARE_WITH_TIMEOUT(attribute(normal, QStringLiteral("data-kondor-sample")).toString(),
                              QStringLiteral("hola"), 10000);

    // The toolbar menu item reaches the extension's onAction callback.
    QMetaObject::invokeMethod(normal.view, "runJavaScript",
                              Q_ARG(QString, QStringLiteral("window.__kondorExtensionActions['sample']('toggle', true);")),
                              Q_ARG(uint, uint(QWebEngineScript::ApplicationWorld)));
    QTRY_COMPARE_WITH_TIMEOUT(attribute(normal, QStringLiteral("data-kondor-action")).toString(),
                              QStringLiteral("toggle:true"), 10000);

    // An excluded path does not run it.
    Page excluded = openPage(normalProfile, server.url(QStringLiteral("/excluded/page")));
    QVERIFY(excluded.view);
    QVERIFY(waitLoaded(excluded));
    QTest::qWait(500);
    QCOMPARE(attribute(excluded, QStringLiteral("data-kondor-sample")).toString(), QString());

    // Private profile: off until the user allows it, then read-only storage.
    Page priv = openPage(privateProfile, server.url());
    QVERIFY(priv.view);
    QVERIFY(waitLoaded(priv));
    QTest::qWait(500);
    QCOMPARE(attribute(priv, QStringLiteral("data-kondor-sample")).toString(), QString());

    manager->applyConfiguration(QStringLiteral("sample"), {}, true, {});
    QTest::qWait(300); // the rebuild of the profiles' scripts is queued
    QMetaObject::invokeMethod(priv.view, "load", Q_ARG(QVariant, server.url(QStringLiteral("/again"))));
    QVERIFY(waitLoaded(priv));
    QTRY_COMPARE_WITH_TIMEOUT(attribute(priv, QStringLiteral("data-kondor-private")).toString(),
                              QStringLiteral("true"), 10000);
    QTRY_VERIFY_WITH_TIMEOUT(attribute(priv, QStringLiteral("data-kondor-storage")).toString().contains(QLatin1String("read-only")),
                             10000);

    // A site the extension is turned off on.
    manager->setSiteEnabled(QStringLiteral("sample"), server.url(), false);
    QTest::qWait(300);
    QMetaObject::invokeMethod(normal.view, "load", Q_ARG(QVariant, server.url(QStringLiteral("/after-toggle"))));
    QVERIFY(waitLoaded(normal));
    QTest::qWait(500);
    QCOMPARE(evaluate(normal, QStringLiteral("location.pathname")).toString(), QStringLiteral("/after-toggle"));
    QCOMPARE(attribute(normal, QStringLiteral("data-kondor-sample")).toString(), QString());

    delete normal.view;
    delete excluded.view;
    delete priv.view;
}

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();

    // Never touch the real profile: settings, data and cache live in a temporary home.
    QTemporaryDir home;
    if (!home.isValid())
        return 1;
    qputenv("XDG_DATA_HOME", home.path().toUtf8());
    qputenv("XDG_CONFIG_HOME", home.path().toUtf8());
    qputenv("XDG_CACHE_HOME", home.path().toUtf8());

    QGuiApplication app(argc, argv);
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));
    QCoreApplication::setOrganizationName(QStringLiteral("KDE-Test"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor-Extensions-Test"));

    TestExtensions test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensions.moc"
