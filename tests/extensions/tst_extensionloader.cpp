#include <QGuiApplication>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickWebEngineProfile>
#include <QSignalSpy>
#include <QTemporaryDir>
#include <QTest>
#include <QUrl>
#include <QtWebEngineCore/qtwebenginecoreglobal.h>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "common/isolatedhome.h"
#include "extensions/extensionloader.h"
#include "pageserver.h"

#if KONDOR_HAVE_EXTENSIONS
#include <QQuickItem>
#include <QWebEngineExtensionManager>
#include <QWebEngineExtensionInfo>

namespace {

const QString testExtensionDirectory = QStringLiteral(KONDOR_TEST_DATA_DIR "/extension");

constexpr const char *markerViewQml = R"(
    import QtQuick
    import QtWebEngine
    WebEngineView {
        property string marker: "pending"
        property bool loaded: false
        onLoadingChanged: function(request) {
            if (request.status === WebEngineView.LoadSucceededStatus)
                loaded = true
        }
        property Timer poll: Timer {
            interval: 200; repeat: true; running: parent.loaded && parent.marker !== "ran"
            onTriggered: parent.runJavaScript(
                "document.documentElement.dataset.kondorTest || 'none'",
                function(result) { parent.marker = result })
        }
    }
)";

QWebEngineExtensionInfo findTestExtension(QQuickWebEngineProfile &profile)
{
    const auto extensions = profile.extensionManager()->extensions();
    for (const QWebEngineExtensionInfo &info : extensions) {
        if (info.name() == QLatin1String("Kondor Test Extension"))
            return info;
    }
    return {};
}

}
#endif

class TestExtensionLoader : public QObject
{
    Q_OBJECT

private slots:
    void loadsAnUnpackedExtension();
    void contentScriptRuns();
    void privateProfilesGetNoExtensions();

private:
#if KONDOR_HAVE_EXTENSIONS
    void loadTestExtension(QQuickWebEngineProfile &profile);
    void verifyContentScriptRuns();
#endif
};

#if KONDOR_HAVE_EXTENSIONS
void TestExtensionLoader::loadTestExtension(QQuickWebEngineProfile &profile)
{
    ExtensionLoader loader;
    QSignalSpy spy(&loader, &ExtensionLoader::loadFinished);
    loader.load(&profile, {testExtensionDirectory});
    QTRY_COMPARE_WITH_TIMEOUT(spy.count(), 1, 20000);
}

void TestExtensionLoader::verifyContentScriptRuns()
{
    QQuickWebEngineProfile profile(QStringLiteral("kondor-extension-test"));
    loadTestExtension(profile);

    PageServer server;
    QVERIFY(server.port() > 0);
    server.start();

    QQmlEngine engine;
    QQmlComponent component(&engine);
    component.setData(markerViewQml, QUrl());
    QScopedPointer<QObject> view(component.create());
    QVERIFY2(view, qPrintable(component.errorString()));
    view->setProperty("profile", QVariant::fromValue(&profile));
    view->setProperty("url", server.url());
    QTRY_COMPARE_WITH_TIMEOUT(view->property("marker").toString(), QStringLiteral("ran"), 20000);
}
#endif

void TestExtensionLoader::loadsAnUnpackedExtension()
{
#if KONDOR_HAVE_EXTENSIONS
    QQuickWebEngineProfile profile(QStringLiteral("kondor-extension-test"));
    ExtensionLoader loader;
    QSignalSpy spy(&loader, &ExtensionLoader::loadFinished);
    loader.load(&profile, {testExtensionDirectory});
    QTRY_COMPARE_WITH_TIMEOUT(spy.count(), 1, 20000);
    QCOMPARE(spy.at(0).at(1).toBool(), true);

    const QWebEngineExtensionInfo info = findTestExtension(profile);
    QVERIFY(info.isLoaded());
    QCOMPARE(info.name(), QStringLiteral("Kondor Test Extension"));
    QVERIFY2(info.actionPopupUrl().toString().endsWith(QStringLiteral("popup.html")),
             qPrintable(info.actionPopupUrl().toString()));
#else
    QSKIP("Qt WebEngine was built without extension support");
#endif
}

void TestExtensionLoader::contentScriptRuns()
{
#if KONDOR_HAVE_EXTENSIONS
    verifyContentScriptRuns();
#else
    QSKIP("Qt WebEngine was built without extension support");
#endif
}

void TestExtensionLoader::privateProfilesGetNoExtensions()
{
#if KONDOR_HAVE_EXTENSIONS
    QQuickWebEngineProfile profile;
    QVERIFY(profile.isOffTheRecord());
    ExtensionLoader loader;
    QSignalSpy spy(&loader, &ExtensionLoader::loadFinished);
    QTest::ignoreMessage(QtWarningMsg, "Extensions are never loaded into private profiles");
    loader.load(&profile, {testExtensionDirectory});
    QCOMPARE(spy.count(), 0);
    QVERIFY(findTestExtension(profile).name().isEmpty());
#else
    QSKIP("Qt WebEngine was built without extension support");
#endif
}

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();
    QTemporaryDir home;
    if (!useIsolatedHome(home))
        return 1;
    QGuiApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE-Test"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor-ExtensionLoader-Test"));
    TestExtensionLoader test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensionloader.moc"
