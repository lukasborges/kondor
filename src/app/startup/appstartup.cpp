#include "app/startup/appstartup.h"

#include "adblock/adblockmanager.h"
#include "app/startup/appidentity.h"
#include "browser/favicons/faviconimageprovider.h"
#include "app/commandline/startupargs.h"
#include "app/windows/windowmanager.h"
#include "browser/profile/profilemanager.h"
#include "extensions/catalog/extensioncatalog.h"
#include "extensions/install/extensionloader.h"
#include "extensions/extensionmanager.h"

#include <QApplication>
#include <QQmlApplicationEngine>

namespace {
SingleInstanceMessage messageFor(const CommandLine &commandLine)
{
    SingleInstanceMessage message;
    message.urls = commandLine.urls;
    message.privateMode = commandLine.isPrivate;
    message.newWindow = commandLine.newWindow;
    message.activationToken = qgetenv("XDG_ACTIVATION_TOKEN");
    return message;
}

void warnAboutSeparateInstance()
{
    qWarning("Kondor: cannot listen for later launches on %s; "
             "running as a separate instance",
             qUtf8Printable(SingleInstance::serverName()));
}

void publishStartupArguments(const CommandLine &commandLine)
{
    StartupArgs *startupArgs = StartupArgs::instance();
    startupArgs->setStartupUrls(commandLine.urls);
    startupArgs->setStartupPrivate(commandLine.isPrivate);
}

void registerProfilesWithExtensions()
{
    ExtensionManager *extensions = ExtensionManager::instance();
    ProfileManager *profiles = ProfileManager::instance();
    QObject::connect(profiles, &ProfileManager::profileCreated, extensions,
                     &ExtensionManager::registerProfile);
    for (QQuickWebEngineProfile *profile : profiles->profiles())
        extensions->registerProfile(profile);
}

void loadUnpackedExtensions(const QStringList &directories)
{
    if (directories.isEmpty())
        return;
    auto *loader = new ExtensionLoader(qApp);
    loader->load(ProfileManager::instance()->defaultProfile(), directories);
}
}

bool forwardsToRunningInstance(SingleInstance &singleInstance, const CommandLine &commandLine)
{
    if (commandLine.newInstance)
        return false;
    const SingleInstance::StartResult result = singleInstance.start(messageFor(commandLine));
    if (result == SingleInstance::StartResult::Failed)
        warnAboutSeparateInstance();
    return result == SingleInstance::StartResult::Forwarded;
}

void startBrowser(QApplication &app, const CommandLine &commandLine)
{
    publishStartupArguments(commandLine);
    setUpLanguageAndStyle(app);
    AdBlockManager::instance()->start();
    registerProfilesWithExtensions();
    loadUnpackedExtensions(commandLine.extensionDirectories);
}

bool openWindows(QQmlApplicationEngine &engine, SingleInstance &singleInstance)
{
    engine.addImageProvider(QStringLiteral("kondor-favicon"), new FaviconImageProvider);
    WindowManager *windowManager = WindowManager::instance();
    windowManager->setEngine(&engine);
    QObject::connect(&singleInstance, &SingleInstance::messageReceived, windowManager,
                     &WindowManager::handleSingleInstanceMessage);
    windowManager->openStartupWindows();
    ExtensionCatalog::instance()->startAutoUpdate();
    return windowManager->windowCount() > 0;
}
