#include <QApplication>
#include <QCommandLineOption>
#include <QCommandLineParser>
#include <QDir>
#include <QGuiApplication>
#include <QIcon>
#include <QLibraryInfo>
#include <QLocale>
#include <QObject>
#include <QQmlApplicationEngine>
#include <QQuickImageProvider>
#include <QQuickStyle>
#include <QTranslator>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "faviconstore.h"
#include "settings.h"
#include "singleinstance.h"
#include "startupargs.h"
#include "startupurl.h"
#include "windowmanager.h"

#include <cstdio>

namespace {
// Serves Kondor's own favicons: `image://kondor-favicon/<page URL>` resolves
// the stored icon for the URL's host (Qt WebEngine's `image://favicon/` only
// knows icon URLs of open views, never page URLs).
class FaviconImageProvider : public QQuickImageProvider
{
public:
    FaviconImageProvider()
        : QQuickImageProvider(QQuickImageProvider::Image)
    {
    }

    QImage requestImage(const QString &id, QSize *size, const QSize &requestedSize) override
    {
        Q_UNUSED(requestedSize)
        const QImage image = FaviconStore::instance()->imageForHost(QUrl(id).host());
        if (size && !image.isNull())
            *size = image.size();
        return image;
    }
};
}

int main(int argc, char *argv[])
{
    // Make sure Qt warnings and errors are printed even when the system's
    // qtlogging.ini silences the debug category.
    qInstallMessageHandler([](QtMsgType type, const QMessageLogContext &, const QString &msg) {
        if (type == QtDebugMsg || type == QtInfoMsg)
            return;
        std::fprintf(stderr, "%s\n", msg.toUtf8().constData());
        std::fflush(stderr);
    });

    // Required by QtWebEngine to share the context with Qt Quick.
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);

    // Must happen before loading anything from WebEngine in QML.
    QtWebEngineQuick::initialize();

    // Inside an AppImage, let the system's xdg-desktop-portal-kde draw the
    // native KDE file dialogs, so KIO workers never have to be bundled.
    if (qEnvironmentVariableIsSet("APPIMAGE")
        && !qEnvironmentVariableIsSet("PLASMA_INTEGRATION_USE_PORTAL")) {
        qputenv("PLASMA_INTEGRATION_USE_PORTAL", "1");
    }

    // QApplication (not QGuiApplication): the KDE platform theme only provides
    // its native file dialogs to a QApplication.
    QApplication app(argc, argv);

    QCoreApplication::setOrganizationName(QStringLiteral("KDE"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor"));
    QCoreApplication::setApplicationVersion(QStringLiteral(PROJECT_VERSION));

    QCommandLineParser parser;
    parser.setApplicationDescription(QStringLiteral("Kondor web browser"));
    parser.addHelpOption();
    parser.addVersionOption();
    const QCommandLineOption privateOption(QStringLiteral("private"),
                                           QStringLiteral("open URLs in a private tab"));
    parser.addOption(privateOption);
    const QCommandLineOption newWindowOption(
        QStringLiteral("new-window"),
        QStringLiteral("open the URLs in a new window of the running instance"));
    parser.addOption(newWindowOption);
    const QCommandLineOption newInstanceOption(
        QStringLiteral("new-instance"),
        QStringLiteral("start a separate process instead of reusing the running one"));
    parser.addOption(newInstanceOption);
    parser.addPositionalArgument(QStringLiteral("urls"),
                                 QStringLiteral("URLs or files to open"),
                                 QStringLiteral("[urls...]"));
    parser.process(app);

    // Resolve the arguments before the QML engine loads so the startup window
    // can open them instead of the home page.
    Settings *settings = Settings::instance();
    QList<QUrl> startupUrls;
    const QStringList arguments = parser.positionalArguments();
    startupUrls.reserve(arguments.size());
    for (const QString &argument : arguments) {
        const QUrl url = startupUrlForArgument(argument, QDir::currentPath(),
                                               QUrl(settings->homePage()),
                                               settings->searchUrlTemplate());
        if (!url.isEmpty())
            startupUrls.append(url);
    }

    const bool startupPrivate = parser.isSet(privateOption);
    StartupArgs *startupArgs = StartupArgs::instance();
    startupArgs->setStartupUrls(startupUrls);
    startupArgs->setStartupPrivate(startupPrivate);

    // One Kondor per user session: a later launch hands its command line to
    // the running process and exits. `--new-instance` opts out (development).
    SingleInstance singleInstance;
    if (!parser.isSet(newInstanceOption)) {
        SingleInstanceMessage message;
        message.urls = startupUrls;
        message.privateMode = startupPrivate;
        message.newWindow = parser.isSet(newWindowOption);
        message.activationToken = qgetenv("XDG_ACTIVATION_TOKEN");

        switch (singleInstance.start(message)) {
        case SingleInstance::StartResult::Forwarded:
            return 0;
        case SingleInstance::StartResult::Listening:
            break;
        case SingleInstance::StartResult::Failed:
            qWarning("Kondor: cannot listen for later launches on %s; "
                     "running as a separate instance",
                     qUtf8Printable(SingleInstance::serverName()));
            break;
        }
    }

    // App identity: the .desktop name (used by Wayland/KWin) and the window icon.
    QGuiApplication::setDesktopFileName(QStringLiteral("kondor"));
    QGuiApplication::setWindowIcon(QIcon(QStringLiteral(":/packaging/kondor.png")));

    // Kondor's own strings; the .qm files are embedded under :/i18n.
    QTranslator appTranslator;
    if (appTranslator.load(QLocale(), QStringLiteral("kondor"), QStringLiteral("_"), QStringLiteral(":/i18n")))
        app.installTranslator(&appTranslator);

    // Qt's own strings (dialogs, standard context menus).
    QTranslator qtTranslator;
    if (qtTranslator.load(QLocale(), QStringLiteral("qt"), QStringLiteral("_"),
                          QLibraryInfo::path(QLibraryInfo::TranslationsPath)))
        app.installTranslator(&qtTranslator);

    // User-visible name of the app, read by QML as Qt.application.displayName.
    //: Application display name: translate "Browser", keep "Kondor"
    QGuiApplication::setApplicationDisplayName(
        QCoreApplication::translate("Kondor", "Kondor Browser"));

    // KDE (Breeze) look applied through the Qt Quick Controls 2 desktop style.
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));
    if (QQuickStyle::name() != QLatin1String("org.kde.desktop"))
        QQuickStyle::setStyle(QStringLiteral("Fusion"));

    QQmlApplicationEngine engine;
    engine.addImageProvider(QStringLiteral("kondor-favicon"), new FaviconImageProvider);

    // The app has no single root window: WindowManager creates them, so tabs
    // can move between windows and Ctrl+N can open another one.
    WindowManager *windowManager = WindowManager::instance();
    windowManager->setEngine(&engine);
    QObject::connect(&singleInstance, &SingleInstance::messageReceived,
                     windowManager, &WindowManager::handleSingleInstanceMessage);
    windowManager->openStartupWindows();

    // Every startup window failed to load: without a window exec() would run
    // forever (quitOnLastWindowClosed never fires), so fail like a QML error in
    // the application root did before.
    if (windowManager->windowCount() == 0)
        return 1;

    return app.exec();
}
