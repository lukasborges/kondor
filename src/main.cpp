#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQuickStyle>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include <cstdio>

int main(int argc, char *argv[])
{
    // Garante que warnings/erros do Qt apareçam mesmo que o qtlogging.ini
    // do sistema silencie a categoria de debug.
    qInstallMessageHandler([](QtMsgType type, const QMessageLogContext &, const QString &msg) {
        if (type == QtDebugMsg || type == QtInfoMsg)
            return;
        std::fprintf(stderr, "%s\n", msg.toUtf8().constData());
        std::fflush(stderr);
    });

    // Requerido pelo QtWebEngine para compartilhar contexto com o Qt Quick.
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);

    // Precisa acontecer antes de carregar qualquer coisa do WebEngine no QML.
    QtWebEngineQuick::initialize();

    QGuiApplication app(argc, argv);

    QCoreApplication::setOrganizationName(QStringLiteral("KDE"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor"));

    // Visual do KDE (Breeze) aplicado via estilo desktop do Qt Quick Controls 2.
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
