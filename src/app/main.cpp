#include <QApplication>
#include <QCommandLineOption>
#include <QCommandLineParser>
#include <QDir>
#include <QFileInfo>
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

#include "adblock/adblockmanager.h"
#include "extensions/extensionloader.h"
#include "extensions/extensioncatalog.h"
#include "extensions/extensionmanager.h"
#include "browser/faviconstore.h"
#include "browser/profilemanager.h"
#include "core/settings.h"
#include "app/singleinstance.h"
#include "app/startupargs.h"
#include "app/startupurl.h"
#include "app/windowmanager.h"

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
    qInstallMessageHandler([](QtMsgType type, const QMessageLogContext &ctx, const QString &msg) {
        // The extension loader reports its results with qInfo().
        const bool extensionLog = ctx.category
            && qstrcmp(ctx.category, "kondor.extensions") == 0;
        if ((type == QtDebugMsg || type == QtInfoMsg) && !extensionLog)
            return;
        std::fprintf(stderr, "%s\n", msg.toUtf8().constData());
        std::fflush(stderr);
    });

    // Required by QtWebEngine to share the context with Qt Quick.
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);

    // Spell checking dictionaries (.bdic) live next to the install or the build.
    // QCoreApplication does not exist yet, so find the executable through /proc.
    if (!qEnvironmentVariableIsSet("QTWEBENGINE_DICTIONARIES_PATH")) {
        const QString appDir =
            QFileInfo(QStringLiteral("/proc/self/exe")).canonicalFilePath().section(
                QLatin1Char('/'), 0, -2);
        const QStringList candidates = {
            appDir + QStringLiteral("/../share/kondor/qtwebengine_dictionaries"),
            appDir + QStringLiteral("/qtwebengine_dictionaries"),
        };
        for (const QString &candidate : candidates) {
            if (QFileInfo(candidate).isDir()) {
                qputenv("QTWEBENGINE_DICTIONARIES_PATH",
                        QDir::cleanPath(candidate).toLocal8Bit());
                break;
            }
        }
    }

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
    const QCommandLineOption loadExtensionOption(
        QStringLiteral("load-extension"),
        QStringLiteral("Load an unpacked extension (developer option). Repeatable; "
                       "not forwarded to a running instance, use with --new-instance"),
        QStringLiteral("dir"));
    parser.addOption(loadExtensionOption);
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
    // Inside a Flatpak the desktop file is renamed to the app id.
    const QString flatpakId = qEnvironmentVariable("FLATPAK_ID");
    QGuiApplication::setDesktopFileName(flatpakId.isEmpty() ? QStringLiteral("kondor") : flatpakId);
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

    // Cached filter lists load in the background; stale ones are refreshed.
    AdBlockManager::instance()->start();

    // Kondor extensions (#107): every profile, now and later, gets the content
    // scripts of the enabled extensions (private ones only when allowed).
    ExtensionManager *extensions = ExtensionManager::instance();
    ProfileManager *profiles = ProfileManager::instance();
    QObject::connect(profiles, &ProfileManager::profileCreated, extensions,
                     &ExtensionManager::registerProfile);
    for (QQuickWebEngineProfile *profile : profiles->profiles())
        extensions->registerProfile(profile);

    // Developer option: unpacked extensions go into the default profile only,
    // before any window loads its pages.
    ExtensionLoader extensionLoader;
    if (parser.isSet(loadExtensionOption))
        extensionLoader.load(ProfileManager::instance()->defaultProfile(),
                             parser.values(loadExtensionOption));

    QQmlApplicationEngine engine;
    engine.addImageProvider(QStringLiteral("kondor-favicon"), new FaviconImageProvider);

    // The app has no single root window: WindowManager creates them, so tabs
    // can move between windows and Ctrl+N can open another one.
    WindowManager *windowManager = WindowManager::instance();
    windowManager->setEngine(&engine);
    QObject::connect(&singleInstance, &SingleInstance::messageReceived,
                     windowManager, &WindowManager::handleSingleInstanceMessage);
    windowManager->openStartupWindows();

    // Catalog extensions update in the background (when the user allows it).
    ExtensionCatalog::instance()->startAutoUpdate();

    // Every startup window failed to load: without a window exec() would run
    // forever (quitOnLastWindowClosed never fires), so fail like a QML error in
    // the application root did before.
    if (windowManager->windowCount() == 0)
        return 1;

    return app.exec();
}
