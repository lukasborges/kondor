#include "extensions/extensionloader.h"

#include <QDir>
#include <QLoggingCategory>
#include <QQuickWebEngineProfile>

#if KONDOR_HAVE_EXTENSIONS
#include <QWebEngineExtensionInfo>
#include <QWebEngineExtensionManager>
#endif

Q_LOGGING_CATEGORY(lcExtensions, "kondor.extensions")

#if KONDOR_HAVE_EXTENSIONS
namespace {

QWebEngineExtensionManager *managerFor(QQuickWebEngineProfile *profile)
{
    if (!profile || profile->isOffTheRecord()) {
        qCWarning(lcExtensions, "Extensions are never loaded into private profiles");
        return nullptr;
    }
    if (!profile->extensionManager())
        qCWarning(lcExtensions, "Extensions are not supported by this Qt WebEngine build");
    return profile->extensionManager();
}

QHash<QString, QString> requestedDirectories(const QStringList &directories)
{
    QHash<QString, QString> requested;
    for (const QString &directory : directories)
        requested.insert(QDir::cleanPath(QDir(directory).absolutePath()), directory);
    return requested;
}

void enableLoadedExtension(const QWebEngineExtensionInfo &info, QWebEngineExtensionManager *manager)
{
    if (!info.isEnabled())
        manager->setExtensionEnabled(info, true);
}

void logLoaded(const QWebEngineExtensionInfo &info)
{
    const QUrl popup = info.actionPopupUrl();
    qCInfo(lcExtensions).noquote()
        << "Extension loaded:" << info.name() << "(" + info.id() + ") popup:"
        << (popup.isEmpty() ? QStringLiteral("none") : popup.toString());
}

void logFailed(const QWebEngineExtensionInfo &info, const QString &directory)
{
    qCInfo(lcExtensions).noquote() << "Extension failed:" << directory + ":" << info.error();
}

}
#endif

ExtensionLoader::ExtensionLoader(QObject *parent)
    : QObject(parent)
{
}

bool ExtensionLoader::isSupported()
{
    return KONDOR_HAVE_EXTENSIONS;
}

void ExtensionLoader::load(QQuickWebEngineProfile *profile, const QStringList &directories)
{
    if (!directories.isEmpty())
        loadInto(profile, directories);
}

#if KONDOR_HAVE_EXTENSIONS

void ExtensionLoader::handleLoadFinished(const QWebEngineExtensionInfo &info,
                                         const QHash<QString, QString> &requested,
                                         QWebEngineExtensionManager *manager)
{
    const QString directory = requested.value(QDir::cleanPath(info.path()), info.path());
    if (info.isLoaded()) {
        enableLoadedExtension(info, manager);
        logLoaded(info);
    } else {
        logFailed(info, directory);
    }
    emit loadFinished(directory, info.isLoaded());
}

void ExtensionLoader::loadInto(QQuickWebEngineProfile *profile, const QStringList &directories)
{
    QWebEngineExtensionManager *manager = managerFor(profile);
    if (!manager)
        return;
    const QHash<QString, QString> requested = requestedDirectories(directories);
    connect(manager, &QWebEngineExtensionManager::loadFinished, this,
            [this, requested, manager](const QWebEngineExtensionInfo &info) {
                handleLoadFinished(info, requested, manager);
            });
    for (const QString &directory : directories)
        manager->loadExtension(QDir(directory).absolutePath());
}

#else

void ExtensionLoader::loadInto(QQuickWebEngineProfile *profile, const QStringList &directories)
{
    Q_UNUSED(profile)
    Q_UNUSED(directories)
    qCWarning(lcExtensions, "Extensions are not supported by this Qt WebEngine build");
}

#endif
