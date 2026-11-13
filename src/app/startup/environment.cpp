#include "app/environment.h"

#include <QCoreApplication>
#include <QDir>
#include <QFileInfo>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

namespace {
QString executableDirectory()
{
    return QFileInfo(QStringLiteral("/proc/self/exe"))
        .canonicalFilePath()
        .section(QLatin1Char('/'), 0, -2);
}

QStringList dictionaryCandidates()
{
    const QString directory = executableDirectory();
    return {
        directory + QStringLiteral("/../share/kondor/qtwebengine_dictionaries"),
        directory + QStringLiteral("/qtwebengine_dictionaries"),
    };
}

void exportDictionariesPath(const QString &path)
{
    qputenv("QTWEBENGINE_DICTIONARIES_PATH", QDir::cleanPath(path).toLocal8Bit());
}

void findDictionaries()
{
    if (qEnvironmentVariableIsSet("QTWEBENGINE_DICTIONARIES_PATH"))
        return;
    for (const QString &candidate : dictionaryCandidates()) {
        if (!QFileInfo(candidate).isDir())
            continue;
        exportDictionariesPath(candidate);
        return;
    }
}

void usePortalInsideAppImage()
{
    const bool isAppImage = qEnvironmentVariableIsSet("APPIMAGE");
    if (isAppImage && !qEnvironmentVariableIsSet("PLASMA_INTEGRATION_USE_PORTAL"))
        qputenv("PLASMA_INTEGRATION_USE_PORTAL", "1");
}
}

void prepareEnvironment()
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    findDictionaries();
    QtWebEngineQuick::initialize();
    usePortalInsideAppImage();
}
