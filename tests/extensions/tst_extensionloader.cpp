#include <QGuiApplication>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QTcpServer>
#include <QTcpSocket>
#include <QQuickWebEngineProfile>
#include <QSignalSpy>
#include <QTemporaryDir>
#include <QTest>
#include <QUrl>
#include <QtWebEngineCore/qtwebenginecoreglobal.h>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "extensions/extensionloader.h"

#if KONDOR_HAVE_EXTENSIONS
#include <QQuickItem>
#include <QWebEngineExtensionManager>
#include <QWebEngineExtensionInfo>
#endif

#if KONDOR_HAVE_EXTENSIONS
static QWebEngineExtensionInfo findTestExtension(QQuickWebEngineProfile &profile)
{
    const auto extensions = profile.extensionManager()->extensions();
    for (const QWebEngineExtensionInfo &info : extensions) {
        if (info.name() == QLatin1String("Kondor Test Extension"))
            return info;
    }
    return {};
}
#endif

class TestExtensionLoader : public QObject
{
    Q_OBJECT

private slots:
    void loadsAnUnpackedExtension();
    void contentScriptRuns();
    void privateProfilesGetNoExtensions();
};

void TestExtensionLoader::loadsAnUnpackedExtension()
{
#if KONDOR_HAVE_EXTENSIONS
    QQuickWebEngineProfile profile(QStringLiteral("kondor-extension-test"));
    ExtensionLoader loader;
    QSignalSpy spy(&loader, &ExtensionLoader::loadFinished);
    const QString dir = QStringLiteral(KONDOR_TEST_DATA_DIR "/extension");
    loader.load(&profile, {dir});
    QTRY_COMPARE_WITH_TIMEOUT(spy.count(), 1, 20000);
    QCOMPARE(spy.at(0).at(1).toBool(), true);

    // Chromium's built-in component extensions are listed too: look ours up.
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
    QQuickWebEngineProfile profile(QStringLiteral("kondor-extension-test"));
    ExtensionLoader loader;
    QSignalSpy spy(&loader, &ExtensionLoader::loadFinished);
    loader.load(&profile, {QStringLiteral(KONDOR_TEST_DATA_DIR "/extension")});
    QTRY_COMPARE_WITH_TIMEOUT(spy.count(), 1, 20000);

    // Extensions cannot touch file: pages without an explicit opt-in, so the
    // page comes from a tiny local HTTP server.
    QTcpServer server;
    QVERIFY(server.listen(QHostAddress::LocalHost));
    connect(&server, &QTcpServer::newConnection, &server, [&server]() {
        while (QTcpSocket *socket = server.nextPendingConnection()) {
            connect(socket, &QTcpSocket::readyRead, socket, [socket]() {
                socket->readAll();
                socket->write("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n"
                              "Connection: close\r\nContent-Length: 30\r\n\r\n"
                              "<html><body>test</body></html>");
                socket->disconnectFromHost();
            });
            connect(socket, &QTcpSocket::disconnected, socket, &QObject::deleteLater);
        }
    });

    QQmlEngine engine;
    QQmlComponent component(&engine);
    component.setData(R"(
        import QtQuick
        import QtWebEngine
        WebEngineView {
            property string marker: "pending"
            property bool loaded: false
            onLoadingChanged: function(request) {
                if (request.status === WebEngineView.LoadSucceededStatus)
                    loaded = true
            }
            // The script runs at document_end; poll until it left its mark.
            property Timer poll: Timer {
                interval: 200; repeat: true; running: parent.loaded && parent.marker !== "ran"
                onTriggered: parent.runJavaScript(
                    "document.documentElement.dataset.kondorTest || 'none'",
                    function(result) { parent.marker = result })
            }
        }
    )", QUrl());
    QScopedPointer<QObject> view(component.create());
    QVERIFY2(view, qPrintable(component.errorString()));
    view->setProperty("profile", QVariant::fromValue(&profile));
    view->setProperty("url", QUrl(QStringLiteral("http://127.0.0.1:%1/").arg(server.serverPort())));
    QTRY_COMPARE_WITH_TIMEOUT(view->property("marker").toString(), QStringLiteral("ran"), 20000);
#else
    QSKIP("Qt WebEngine was built without extension support");
#endif
}

void TestExtensionLoader::privateProfilesGetNoExtensions()
{
#if KONDOR_HAVE_EXTENSIONS
    QQuickWebEngineProfile profile; // off the record
    QVERIFY(profile.isOffTheRecord());
    ExtensionLoader loader;
    QSignalSpy spy(&loader, &ExtensionLoader::loadFinished);
    QTest::ignoreMessage(QtWarningMsg, "Extensions are never loaded into private profiles");
    loader.load(&profile, {QStringLiteral(KONDOR_TEST_DATA_DIR "/extension")});
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
    // Keep the named test profiles out of the real home.
    QTemporaryDir home;
    if (!home.isValid())
        return 1;
    qputenv("XDG_DATA_HOME", home.path().toUtf8());
    qputenv("XDG_CONFIG_HOME", home.path().toUtf8());
    qputenv("XDG_CACHE_HOME", home.path().toUtf8());
    QGuiApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE-Test"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor-ExtensionLoader-Test"));
    TestExtensionLoader test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensionloader.moc"
