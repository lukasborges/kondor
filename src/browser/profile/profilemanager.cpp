#include "browser/profilemanager.h"

#include "browser/addressresolver.h"
#include "browser/pagescripts.h"
#include "browser/profilesetup.h"
#include "core/settings.h"
#include "history/historymanager.h"

#include <QCoreApplication>
#include <QQuickWebEngineProfile>
#include <QWebEngineCookieStore>

namespace {
void clearCookiesAndCache(QQuickWebEngineProfile *profile)
{
    profile->clearHttpCache();
    if (QWebEngineCookieStore *store = profile->cookieStore())
        store->deleteAllCookies();
}

void blockThirdPartyCookiesWhenConfigured(QQuickWebEngineProfile *profile)
{
    QWebEngineCookieStore *store = profile->cookieStore();
    if (!store)
        return;
    store->setCookieFilter([](const QWebEngineCookieStore::FilterRequest &request) {
        return !request.thirdParty || !Settings::instance()->blockThirdPartyCookies();
    });
}
}

ProfileManager *ProfileManager::instance()
{
    static ProfileManager *manager = new ProfileManager;
    return manager;
}

ProfileManager *ProfileManager::create(QQmlEngine *, QJSEngine *)
{
    return instance();
}

ProfileManager::ProfileManager(QObject *parent)
    : QObject(parent)
{
    connectSettings();
    connect(QCoreApplication::instance(), &QCoreApplication::aboutToQuit, this,
            &ProfileManager::clearDataOnExit);
}

void ProfileManager::connectSettings()
{
    Settings *settings = Settings::instance();
    connect(settings, &Settings::homePageChanged, this, &ProfileManager::homePageChanged);
    connect(settings, &Settings::downloadDirectoryChanged, this,
            &ProfileManager::applyDownloadDirectory);
    connect(settings, &Settings::spellCheckEnabledChanged, this, &ProfileManager::applySpellCheck);
    connect(settings, &Settings::spellCheckLanguagesChanged, this,
            &ProfileManager::applySpellCheck);
}

void ProfileManager::forEachProfile(const std::function<void(QQuickWebEngineProfile *)> &action) const
{
    for (QQuickWebEngineProfile *profile : profiles())
        action(profile);
}

void ProfileManager::applyDownloadDirectory()
{
    const QString directory = Settings::instance()->downloadDirectory();
    forEachProfile([directory](QQuickWebEngineProfile *profile) {
        profile->setDownloadPath(directory);
    });
}

void ProfileManager::applySpellCheck()
{
    forEachProfile(&ProfileSetup::applySpellCheck);
}

void ProfileManager::clearDataOnExit()
{
    if (!Settings::instance()->clearDataOnExit())
        return;
    if (m_defaultProfile)
        clearCookiesAndCache(m_defaultProfile);
    HistoryManager::instance()->clearAll();
}

QQuickWebEngineProfile *ProfileManager::defaultProfile()
{
    if (!m_defaultProfile)
        m_defaultProfile = createPersistentProfile();
    return m_defaultProfile;
}

QQuickWebEngineProfile *ProfileManager::createPersistentProfile()
{
    auto *profile = new QQuickWebEngineProfile(QStringLiteral("kondor"), this);
    profile->setPersistentCookiesPolicy(QQuickWebEngineProfile::AllowPersistentCookies);
    profile->setPersistentPermissionsPolicy(
            QQuickWebEngineProfile::PersistentPermissionsPolicy::StoreOnDisk);
    setupProfile(profile);
    blockThirdPartyCookiesWhenConfigured(profile);
    return profile;
}

QQuickWebEngineProfile *ProfileManager::createPrivateProfile()
{
    auto *profile = new QQuickWebEngineProfile(this);
    profile->setPersistentCookiesPolicy(QQuickWebEngineProfile::NoPersistentCookies);
    profile->setPersistentPermissionsPolicy(
            QQuickWebEngineProfile::PersistentPermissionsPolicy::StoreInMemory);
    m_privateProfiles.append(profile);
    connect(profile, &QObject::destroyed, this,
            [this, profile] { m_privateProfiles.removeOne(profile); });
    setupProfile(profile);
    return profile;
}

void ProfileManager::setupProfile(QQuickWebEngineProfile *profile)
{
    PageScripts::install(profile);
    ProfileSetup::apply(profile);
    connect(profile, &QObject::destroyed, this,
            [this, profile] { m_certificateOverrides.forget(profile); });
    emit profileCreated(profile);
}

void ProfileManager::clearCookiesAndCacheNow()
{
    clearCookiesAndCache(defaultProfile());
}

void ProfileManager::markCertificateOverridden(QQuickWebEngineProfile *profile, const QString &host)
{
    m_certificateOverrides.mark(profile, host);
}

bool ProfileManager::isCertificateOverridden(QQuickWebEngineProfile *profile,
                                             const QString &host) const
{
    return m_certificateOverrides.isOverridden(profile, host);
}

QList<QQuickWebEngineProfile *> ProfileManager::profiles() const
{
    QList<QQuickWebEngineProfile *> list;
    if (m_defaultProfile)
        list.append(m_defaultProfile);
    list.append(m_privateProfiles);
    return list;
}

QString ProfileManager::homePage() const
{
    return Settings::instance()->homePage();
}

QUrl ProfileManager::resolveAddress(const QString &text) const
{
    return ::resolveAddress(text, QUrl(homePage()), Settings::instance()->searchUrlTemplate());
}

QUrl ProfileManager::addressUrl(const QString &text) const
{
    return ::addressUrl(text);
}

QUrl ProfileManager::searchUrl(const QString &text) const
{
    return ::searchUrl(text, Settings::instance()->searchUrlTemplate());
}
