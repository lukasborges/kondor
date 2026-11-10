#include "profilemanager.h"

#include <QFile>
#include <QWebEngineScript>

#include "adblock/adblockmanager.h"
#include "addressresolver.h"
#include "downloadmanager.h"
#include "historymanager.h"
#include "notifier.h"
#include "settings.h"

#include <QCoreApplication>
#include <QLocale>
#include <QQuickWebEngineDownloadRequest>
#include <QQuickWebEngineProfile>
#include <QRegularExpression>
#include <QWebEngineCookieStore>
#include <QWebEngineNotification>

#include <utility>

ProfileManager *ProfileManager::instance()
{
    static ProfileManager *manager = new ProfileManager;
    return manager;
}

ProfileManager *ProfileManager::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(engine)
    Q_UNUSED(jsEngine)
    return instance();
}

ProfileManager::ProfileManager(QObject *parent)
    : QObject(parent)
{
    Settings *settings = Settings::instance();

    // Settings are the single source of truth; ProfileManager only forwards them.
    connect(settings, &Settings::homePageChanged,
            this, &ProfileManager::homePageChanged);

    connect(settings, &Settings::downloadDirectoryChanged, this, [this]() {
        const QString directory = Settings::instance()->downloadDirectory();
        if (m_defaultProfile)
            m_defaultProfile->setDownloadPath(directory);
        for (QQuickWebEngineProfile *profile : std::as_const(m_privateProfiles))
            profile->setDownloadPath(directory);
    });

    const auto applySpellCheck = [this]() {
        if (m_defaultProfile)
            applySpellCheckSettings(m_defaultProfile);
        for (QQuickWebEngineProfile *profile : std::as_const(m_privateProfiles))
            applySpellCheckSettings(profile);
    };
    connect(settings, &Settings::spellCheckEnabledChanged, this, applySpellCheck);
    connect(settings, &Settings::spellCheckLanguagesChanged, this, applySpellCheck);

    connect(QCoreApplication::instance(), &QCoreApplication::aboutToQuit, this, [this]() {
        if (!Settings::instance()->clearDataOnExit())
            return;
        if (m_defaultProfile) {
            m_defaultProfile->clearHttpCache();
            if (QWebEngineCookieStore *store = m_defaultProfile->cookieStore())
                store->deleteAllCookies();
        }
        HistoryManager::instance()->clearAll();
    });
}

QQuickWebEngineProfile *ProfileManager::defaultProfile()
{
    if (!m_defaultProfile) {
        // A storage name creates a persistent (on-the-record) profile.
        m_defaultProfile = new QQuickWebEngineProfile(QStringLiteral("kondor"), this);
        m_defaultProfile->setPersistentCookiesPolicy(QQuickWebEngineProfile::AllowPersistentCookies);
        // Site permission decisions survive restarts for normal tabs.
        m_defaultProfile->setPersistentPermissionsPolicy(
                QQuickWebEngineProfile::PersistentPermissionsPolicy::StoreOnDisk);
        setupProfile(m_defaultProfile);
        // Only the persistent profile keeps cookies across sessions, so the
        // third-party cookie preference is enforced there.
        applyThirdPartyCookieFilter(m_defaultProfile);
    }
    return m_defaultProfile;
}

QQuickWebEngineProfile *ProfileManager::createPrivateProfile()
{
    // No storage name: off-the-record profile (private), isolated from the rest.
    auto *profile = new QQuickWebEngineProfile(this);
    profile->setPersistentCookiesPolicy(QQuickWebEngineProfile::NoPersistentCookies);
    // A private tab may keep its answers for the session, never on disk.
    profile->setPersistentPermissionsPolicy(
            QQuickWebEngineProfile::PersistentPermissionsPolicy::StoreInMemory);
    m_privateProfiles.append(profile);
    connect(profile, &QObject::destroyed, this, [this, profile]() {
        m_privateProfiles.removeOne(profile);
    });
    setupProfile(profile);
    return profile;
}

void ProfileManager::installPasswordScript(QQuickWebEngineProfile *profile)
{
    // Persistent profile only: private tabs never get the password script.
    if (profile->isOffTheRecord())
        return;
    QFile webChannelJs(QStringLiteral(":/qtwebchannel/qwebchannel.js"));
    QFile passwordsJs(QStringLiteral(":/scripts/passwords.js"));
    if (!webChannelJs.open(QIODevice::ReadOnly) || !passwordsJs.open(QIODevice::ReadOnly)) {
        qWarning("Password script resources not found: autofill is off");
        return;
    }
    QWebEngineScript script;
    script.setName(QStringLiteral("kondor-passwords"));
    script.setSourceCode(QString::fromUtf8(webChannelJs.readAll()) + QLatin1Char('\n')
                         + QString::fromUtf8(passwordsJs.readAll()));
    script.setInjectionPoint(QWebEngineScript::DocumentReady);
    script.setWorldId(QWebEngineScript::ApplicationWorld);
    script.setRunsOnSubFrames(true);

    QObject *collection = profile->property("userScripts").value<QObject *>();
    if (!collection
        || !QMetaObject::invokeMethod(collection, "insert", Q_ARG(QWebEngineScript, script)))
        qWarning("Cannot install the password script: autofill is off");
}

void ProfileManager::setupProfile(QQuickWebEngineProfile *profile)
{
    installPasswordScript(profile);

    // User-Agent: keep Chromium (compatibility), but drop the "QtWebEngine"
    // token that makes some sites treat the browser as unknown.
    QString userAgent = profile->httpUserAgent();
    static const QRegularExpression qtWebEngineToken(QStringLiteral("QtWebEngine/[^ ]+"));
    userAgent.replace(qtWebEngineToken, QStringLiteral("Kondor/0.1"));
    profile->setHttpUserAgent(userAgent);

    // Sites get content in the user's language.
    profile->setHttpAcceptLanguage(QLocale().bcp47Name());

    profile->setDownloadPath(Settings::instance()->downloadDirectory());
    applySpellCheckSettings(profile);
    AdBlockManager::instance()->install(profile);

    // Downloads are owned by the shared DownloadManager; private profiles pass
    // the flag so their entries never outlive the session.
    connect(profile, &QQuickWebEngineProfile::downloadRequested, DownloadManager::instance(),
            [profile](QQuickWebEngineDownloadRequest *download) {
                DownloadManager::instance()->handleRequest(download, profile->isOffTheRecord());
            });

    // A page only reaches this signal after the site was allowed to show
    // notifications. Route them to the desktop through the shared Notifier.
    connect(profile, &QQuickWebEngineProfile::presentNotification, this,
            [](QWebEngineNotification *notification) {
                if (!notification)
                    return;
                Notifier::instance()->notify(notification->title(), notification->message(),
                                             QStringLiteral("preferences-desktop-notification"));
                notification->show();
            });

    // Certificate overrides are kept per profile and never written to disk; a
    // profile that goes away (a private tab's) takes its hosts with it.
    connect(profile, &QObject::destroyed, this, [this, profile]() {
        m_overriddenCertificateHosts.remove(profile);
    });
}

void ProfileManager::applySpellCheckSettings(QQuickWebEngineProfile *profile)
{
    Settings *settings = Settings::instance();
    profile->setSpellCheckLanguages(settings->spellCheckLanguages());
    profile->setSpellCheckEnabled(settings->spellCheckEnabled());
}

void ProfileManager::applyThirdPartyCookieFilter(QQuickWebEngineProfile *profile)
{
    QWebEngineCookieStore *store = profile->cookieStore();
    if (!store)
        return;
    // Read the setting per request, so toggling it needs no reconnect.
    store->setCookieFilter([](const QWebEngineCookieStore::FilterRequest &request) {
        return !request.thirdParty || !Settings::instance()->blockThirdPartyCookies();
    });
}

void ProfileManager::clearCookiesAndCacheNow()
{
    QQuickWebEngineProfile *profile = defaultProfile();
    profile->clearHttpCache();
    if (QWebEngineCookieStore *store = profile->cookieStore())
        store->deleteAllCookies();
}

void ProfileManager::markCertificateOverridden(QQuickWebEngineProfile *profile, const QString &host)
{
    if (!profile || host.isEmpty())
        return;
    m_overriddenCertificateHosts[profile].insert(host.toLower());
}

bool ProfileManager::isCertificateOverridden(QQuickWebEngineProfile *profile, const QString &host) const
{
    if (!profile || host.isEmpty())
        return false;
    const auto it = m_overriddenCertificateHosts.constFind(profile);
    return it != m_overriddenCertificateHosts.constEnd() && it->contains(host.toLower());
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
