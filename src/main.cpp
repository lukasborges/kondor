#include <QCommandLineOption>
#include <QCommandLineParser>
#include <QDir>
#include <QGuiApplication>
#include <QIcon>
#include <QLibraryInfo>
#include <QLocale>
#include <QQmlApplicationEngine>
#include <QQuickStyle>
#include <QTranslator>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "settings.h"
#include "startupargs.h"
#include "startupurl.h"

#include <cstdio>

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

    QGuiApplication app(argc, argv);

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
    parser.addPositionalArgument(QStringLiteral("urls"),
                                 QStringLiteral("URLs or files to open"),
                                 QStringLiteral("[urls...]"));
    parser.process(app);

    // Resolve the arguments before the QML engine loads so Main.qml can open
    // them instead of the home page.
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

    StartupArgs *startupArgs = StartupArgs::instance();
    startupArgs->setStartupUrls(startupUrls);
    startupArgs->setStartupPrivate(parser.isSet(privateOption));

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
    QObject::connect(
        &engine, &QQmlApplicationEngine::objectCreationFailed,
        &app, []() { QCoreApplication::exit(1); },
        Qt::QueuedConnection);

    engine.loadFromModule(QStringLiteral("Kondor"), QStringLiteral("Main"));

    return app.exec();
}
