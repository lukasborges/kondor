#include "app/appidentity.h"

#include <QApplication>
#include <QIcon>
#include <QLibraryInfo>
#include <QLocale>
#include <QQuickStyle>
#include <QTranslator>

namespace {
void installTranslator(QApplication &app, const QString &name, const QString &directory)
{
    auto *translator = new QTranslator(&app);
    if (translator->load(QLocale(), name, QStringLiteral("_"), directory))
        app.installTranslator(translator);
}

void setDisplayName()
{
    //: Application display name: translate "Browser", keep "Kondor"
    QGuiApplication::setApplicationDisplayName(
        QCoreApplication::translate("Kondor", "Kondor Browser"));
}

void useDesktopStyle()
{
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));
    if (QQuickStyle::name() != QLatin1String("org.kde.desktop"))
        QQuickStyle::setStyle(QStringLiteral("Fusion"));
}

QString desktopFileName()
{
    const QString flatpakId = qEnvironmentVariable("FLATPAK_ID");
    return flatpakId.isEmpty() ? QStringLiteral("kondor") : flatpakId;
}
}

void setUpIdentity()
{
    QCoreApplication::setOrganizationName(QStringLiteral("KDE"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor"));
    QCoreApplication::setApplicationVersion(QStringLiteral(PROJECT_VERSION));
    QGuiApplication::setDesktopFileName(desktopFileName());
    QGuiApplication::setWindowIcon(QIcon(QStringLiteral(":/packaging/kondor.png")));
}

void setUpLanguageAndStyle(QApplication &app)
{
    installTranslator(app, QStringLiteral("kondor"), QStringLiteral(":/i18n"));
    installTranslator(app, QStringLiteral("qt"),
                      QLibraryInfo::path(QLibraryInfo::TranslationsPath));
    setDisplayName();
    useDesktopStyle();
}
