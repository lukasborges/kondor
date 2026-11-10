#include "extensionloader.h"

#include <QDir>
#include <QLoggingCategory>
#include <QQuickWebEngineProfile>
#include <QtWebEngineCore/qtwebenginecoreglobal.h>

#if QT_CONFIG(webengine_extensions)
#include <QWebEngineExtensionInfo>
#include <QWebEngineExtensionManager>
#endif

Q_LOGGING_CATEGORY(lcExtensions, "kondor.extensions")

ExtensionLoader::ExtensionLoader(QObject *parent)
    : QObject(parent)
{
}

bool ExtensionLoader::isSupported()
{
#if QT_CONFIG(webengine_extensions)
    return true;
#else
    return false;
#endif
}

void ExtensionLoader::load(QQuickWebEngineProfile *profile, const QStringList &directories)
{
    if (directories.isEmpty())
        return;

#if QT_CONFIG(webengine_extensions)
    if (!profile || profile->isOffTheRecord()) {
        qCWarning(lcExtensions, "Extensions are never loaded into private profiles");
        return;
    }
    QWebEngineExtensionManager *manager = profile->extensionManager();
    if (!manager) {
        qCWarning(lcExtensions, "Extensions are not supported by this Qt WebEngine build");
        return;
    }

    // loadFinished carries only the extension info; match it to the requested
    // directory by canonical path to report failures with the user's argument.
    QHash<QString, QString> pending;
    for (const QString &directory : directories) {
        const QString absolute = QDir(directory).absolutePath();
        pending.insert(QDir::cleanPath(absolute), directory);
    }

    connect(manager, &QWebEngineExtensionManager::loadFinished, this,
            [this, pending, manager](const QWebEngineExtensionInfo &info) {
                const QString key = QDir::cleanPath(info.path());
                const QString directory = pending.value(key, info.path());
                if (info.isLoaded()) {
                    // A freshly loaded extension is not enabled yet, and a
                    // disabled one injects no content scripts.
                    if (!info.isEnabled())
                        manager->setExtensionEnabled(info, true);
                    const QUrl popup = info.actionPopupUrl();
                    qCInfo(lcExtensions).noquote()
                        << "Extension loaded:" << info.name() << "(" + info.id() + ") popup:"
                        << (popup.isEmpty() ? QStringLiteral("none") : popup.toString());
                } else {
                    qCInfo(lcExtensions).noquote()
                        << "Extension failed:" << directory + ":" << info.error();
                }
                emit loadFinished(directory, info.isLoaded());
            });

    for (const QString &directory : directories)
        manager->loadExtension(QDir(directory).absolutePath());
#else
    Q_UNUSED(profile)
    qCWarning(lcExtensions, "Extensions are not supported by this Qt WebEngine build");
#endif
}
