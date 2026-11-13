#include "browser/profile/profilesetup.h"

#include "adblock/adblockmanager.h"
#include "core/notifier.h"
#include "core/settings/settings.h"
#include "downloads/downloadmanager.h"

#include <QLocale>
#include <QQuickWebEngineDownloadRequest>
#include <QQuickWebEngineProfile>
#include <QRegularExpression>
#include <QWebEngineNotification>

namespace {
void applyUserAgent(QQuickWebEngineProfile *profile)
{
    static const QRegularExpression qtWebEngineToken(QStringLiteral("QtWebEngine/[^ ]+"));
    QString userAgent = profile->httpUserAgent();
    userAgent.replace(qtWebEngineToken, QStringLiteral("Kondor/0.1"));
    profile->setHttpUserAgent(userAgent);
}

void routeDownloads(QQuickWebEngineProfile *profile)
{
    QObject::connect(profile, &QQuickWebEngineProfile::downloadRequested,
                     DownloadManager::instance(),
                     [profile](QQuickWebEngineDownloadRequest *download) {
                         DownloadManager::instance()->handleRequest(download,
                                                                    profile->isOffTheRecord());
                     });
}

void showNotification(QWebEngineNotification *notification)
{
    if (!notification)
        return;
    Notifier::instance()->notify(notification->title(), notification->message(),
                                 QStringLiteral("preferences-desktop-notification"));
    notification->show();
}

void routeNotifications(QQuickWebEngineProfile *profile)
{
    QObject::connect(profile, &QQuickWebEngineProfile::presentNotification, profile,
                     &showNotification);
}
}

void ProfileSetup::applySpellCheck(QQuickWebEngineProfile *profile)
{
    Settings *settings = Settings::instance();
    profile->setSpellCheckLanguages(settings->spellCheckLanguages());
    profile->setSpellCheckEnabled(settings->spellCheckEnabled());
}

void ProfileSetup::apply(QQuickWebEngineProfile *profile)
{
    applyUserAgent(profile);
    profile->setHttpAcceptLanguage(QLocale().bcp47Name());
    profile->setDownloadPath(Settings::instance()->downloadDirectory());
    applySpellCheck(profile);
    AdBlockManager::instance()->install(profile);
    routeDownloads(profile);
    routeNotifications(profile);
}
