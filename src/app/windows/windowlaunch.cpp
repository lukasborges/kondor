#include "app/windows/windowmanager.h"

#include "app/commandline/extensionpackages.h"
#include "app/commandline/startupargs.h"
#include "app/instance/windowactivation.h"
#include "browser/session/sessionmanager.h"
#include "core/settings/settings.h"
#include "extensions/extensionmanager.h"

namespace {
WindowContents restoredContents(const SessionWindow &state)
{
    WindowContents contents;
    contents.currentIndex = state.currentIndex;
    for (const SessionTab &tab : state.tabs) {
        contents.urls.append(tab.url);
        contents.titles.append(tab.title);
    }
    return contents;
}

bool shouldRestoreSession()
{
    return Settings::instance()->startupBehavior() == QLatin1String("restore");
}
}

void WindowManager::handleSingleInstanceMessage(const SingleInstanceMessage &message)
{
    QList<QUrl> urls = message.urls;
    const QStringList packages = takeExtensionPackages(urls);
    QObject *window = showPackages(packages, openUrlsForLaunch(message, urls));
    if (window)
        raiseWindow(window, message.activationToken);
}

QObject *WindowManager::openUrlsForLaunch(const SingleInstanceMessage &message,
                                          const QList<QUrl> &urls)
{
    QObject *window = message.newWindow ? nullptr : windowForRequest(message.privateMode);
    if (!window)
        return createWindow({message.privateMode, urls, {}, -1});
    if (!urls.isEmpty())
        addTabs(window, urls);
    return window;
}

void WindowManager::addTabs(QObject *window, const QList<QUrl> &urls)
{
    const bool isAdded = QMetaObject::invokeMethod(window, "openUrlsInNewTabs",
                                                   Q_ARG(QVariant, QVariant::fromValue(urls)));
    if (!isAdded)
        qWarning("Kondor: cannot add tabs to the running window");
}

QObject *WindowManager::normalWindow()
{
    QObject *window = windowForRequest(false);
    return window ? window : createWindow({});
}

QObject *WindowManager::showPackages(const QStringList &packages, QObject *window)
{
    if (packages.isEmpty())
        return window;
    QObject *normal = normalWindow();
    showExtensionPackage(normal, packages.first());
    return window ? window : normal;
}

void WindowManager::showExtensionPackage(QObject *window, const QString &path)
{
    ExtensionManager::instance()->inspectFile(path);
    const QVariant page = QStringLiteral("extensions");
    if (window && !QMetaObject::invokeMethod(window, "openSettingsPage", Q_ARG(QVariant, page)))
        qWarning("Kondor: cannot open the extensions settings");
}

void WindowManager::openStartupWindows()
{
    QList<QUrl> urls = StartupArgs::instance()->startupUrls();
    const QStringList packages = takeExtensionPackages(urls);
    bool isOpened = openRestoredWindows();
    isOpened = openCommandLineWindow(urls) || isOpened;
    if (!isOpened)
        createWindow({});
    if (!packages.isEmpty())
        showExtensionPackage(windowForRequest(false), packages.first());
}

bool WindowManager::openRestoredWindows()
{
    if (!shouldRestoreSession())
        return false;
    bool isOpened = false;
    const QList<SessionWindow> windows = SessionManager::instance()->savedWindows();
    for (const SessionWindow &state : windows)
        isOpened = createWindow(restoredContents(state)) || isOpened;
    return isOpened;
}

bool WindowManager::openCommandLineWindow(const QList<QUrl> &urls)
{
    const bool isPrivate = StartupArgs::instance()->startupPrivate();
    if (urls.isEmpty() && !isPrivate)
        return false;
    return createWindow({isPrivate, urls, {}, -1}) != nullptr;
}
