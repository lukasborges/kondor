#include "aboutinfo.h"

#include <QCoreApplication>
#include <QFile>
#include <QGuiApplication>
#include <QSysInfo>
#include <QtGlobal>
#include <QtWebEngineCore/qtwebenginecoreglobal.h>

AboutInfo *AboutInfo::instance()
{
    static AboutInfo *info = new AboutInfo;
    return info;
}

AboutInfo *AboutInfo::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(engine)
    Q_UNUSED(jsEngine)
    return instance();
}

AboutInfo::AboutInfo(QObject *parent)
    : QObject(parent)
{
    // Embedded through qt_add_resources, so no file is needed at run time.
    QFile license(QStringLiteral(":/LICENSE"));
    if (license.open(QIODevice::ReadOnly | QIODevice::Text))
        m_licenseText = QString::fromUtf8(license.readAll()).trimmed();
}

QString AboutInfo::version() const
{
    return QCoreApplication::applicationVersion();
}

QString AboutInfo::qtRuntimeVersion() const
{
    return QString::fromLatin1(qVersion());
}

QString AboutInfo::qtBuildVersion() const
{
    return QString::fromLatin1(QT_VERSION_STR);
}

QString AboutInfo::webEngineVersion() const
{
    return QString::fromLatin1(qWebEngineVersion());
}

QString AboutInfo::chromiumVersion() const
{
    return QString::fromLatin1(qWebEngineChromiumVersion());
}

QString AboutInfo::windowingSystem() const
{
    const QString platform = QGuiApplication::platformName();
    if (platform.startsWith(QLatin1String("wayland")))
        return QStringLiteral("Wayland");
    if (platform == QLatin1String("xcb"))
        return QStringLiteral("X11");
    return platform;
}

QString AboutInfo::operatingSystem() const
{
    return QSysInfo::prettyProductName();
}

QString AboutInfo::licenseText() const
{
    return m_licenseText;
}
