#include <QGuiApplication>
#include <QJsonDocument>
#include <QTemporaryDir>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include <KZip>

#include "browser/tabs/tab.h"
#include "extensions/bridge/extensionbridge.h"
#include "extensions/bridge/extensioncall.h"
#include "extensions/extensionmanager.h"

class TestExtensionCall : public QObject
{
    Q_OBJECT

private slots:
    void parsesTheRequestObject();
    void malformedRequestGivesEmptyFields();
    void bridgeRejectsUnknownTabsMethodAfterPermissionCheck();
};

namespace {

QString sampleDirectory()
{
    return QStringLiteral(KONDOR_TEST_DATA_DIR "/extensions/sample");
}

bool installSample(const QString &zipPath)
{
    KZip zip(zipPath);
    if (!zip.open(QIODevice::WriteOnly) || !zip.addLocalDirectory(sampleDirectory(), QString()) || !zip.close())
        return false;
    return ExtensionManager::instance()->installPackage({zipPath, QStringLiteral("file")}, QStringLiteral("sample")).isInstalled;
}

QString tokenOfSample()
{
    const QString source = ExtensionManager::instance()->scriptSource(QStringLiteral("sample"), 0, true);
    const QString marker = QStringLiteral("\"token\":\"");
    const int from = source.indexOf(marker) + marker.size();
    return source.mid(from, source.indexOf(QLatin1Char('"'), from) - from);
}

QJsonObject reply(ExtensionBridge &bridge, const ExtensionCall &call)
{
    return QJsonDocument::fromJson(bridge.request(call).toUtf8()).object();
}

}

void TestExtensionCall::parsesTheRequestObject()
{
    const ExtensionCall call = parseExtensionCall(
        QStringLiteral(R"({"id":"sample","token":"t","method":"tabs.back","arguments":[1,"a"]})"));
    QCOMPARE(call.extensionId, QStringLiteral("sample"));
    QCOMPARE(call.token, QStringLiteral("t"));
    QCOMPARE(call.method, QStringLiteral("tabs.back"));
    QCOMPARE(call.arguments.size(), 2);
}

void TestExtensionCall::malformedRequestGivesEmptyFields()
{
    for (const QString &json : {QStringLiteral("not json"), QStringLiteral("[]"),
                                QStringLiteral(R"({"id":3,"arguments":"x"})")}) {
        const ExtensionCall call = parseExtensionCall(json);
        QVERIFY(call.extensionId.isEmpty() && call.token.isEmpty() && call.method.isEmpty());
        QVERIFY(call.arguments.isEmpty());
    }
}

void TestExtensionCall::bridgeRejectsUnknownTabsMethodAfterPermissionCheck()
{
    QTemporaryDir work;
    QVERIFY(installSample(work.filePath(QStringLiteral("sample.kondorext"))));
    ExtensionManager::instance()->applyConfiguration(QStringLiteral("sample"), {{QStringLiteral("privateAllowed"), true}});
    Tab tab(nullptr);
    ExtensionBridge bridge;
    bridge.setTab(&tab);
    const ExtensionCall call{QStringLiteral("sample"), tokenOfSample(), QStringLiteral("tabs.nope"), {}};
    QCOMPARE(reply(bridge, call).value(QStringLiteral("error")).toString(), QStringLiteral("Unknown method: tabs.nope"));
    ExtensionManager::instance()->remove(QStringLiteral("sample"));
}

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();
    QTemporaryDir home;
    if (!home.isValid())
        return 1;
    for (const char *name : {"XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"})
        qputenv(name, home.path().toUtf8());
    QGuiApplication app(argc, argv);
    TestExtensionCall test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensioncall.moc"
