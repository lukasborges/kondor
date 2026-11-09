#include "profilemanager.h"

#include "downloadmanager.h"
#include "historymanager.h"
#include "settings.h"

#include <QCoreApplication>
#include <QQuickWebEngineDownloadRequest>
#include <QRegularExpression>
#include <QWebEngineCookieStore>

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
    m_privateProfiles.append(profile);
    connect(profile, &QObject::destroyed, this, [this, profile]() {
        m_privateProfiles.removeOne(profile);
    });
    setupProfile(profile);
    return profile;
}

void ProfileManager::setupProfile(QQuickWebEngineProfile *profile)
{
    // User-Agent: keep Chromium (compatibility), but drop the "QtWebEngine"
    // token that makes some sites treat the browser as unknown.
    QString userAgent = profile->httpUserAgent();
    static const QRegularExpression qtWebEngineToken(QStringLiteral("QtWebEngine/[^ ]+"));
    userAgent.replace(qtWebEngineToken, QStringLiteral("Kondor/0.1"));
    profile->setHttpUserAgent(userAgent);

    profile->setDownloadPath(Settings::instance()->downloadDirectory());

    // Downloads are owned by the shared DownloadManager; private profiles pass
    // the flag so their entries never outlive the session.
    connect(profile, &QQuickWebEngineProfile::downloadRequested, DownloadManager::instance(),
            [profile](QQuickWebEngineDownloadRequest *download) {
                DownloadManager::instance()->handleRequest(download, profile->isOffTheRecord());
            });
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

QString ProfileManager::homePage() const
{
    return Settings::instance()->homePage();
}

QUrl ProfileManager::resolveAddress(const QString &text) const
{
    const QString input = text.trimmed();
    if (input.isEmpty())
        return QUrl(homePage());

    if (input.contains(QLatin1String("://"))
        || input.startsWith(QLatin1String("about:"))
        || input.startsWith(QLatin1String("data:"))) {
        return QUrl::fromUserInput(input);
    }

    // IP, localhost or domain with a TLD -> assume https.
    static const QRegularExpression hostRe(QStringLiteral(
        R"(^(([0-9]{1,3}\.){3}[0-9]{1,3}|localhost|[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})(:\d+)?(/.*)?$)"));
    if (hostRe.match(input).hasMatch())
        return QUrl(QStringLiteral("https://") + input);

    // Otherwise search with the configured engine.
    QString url = Settings::instance()->searchUrlTemplate();
    url.replace(QLatin1String("%1"), QString::fromUtf8(QUrl::toPercentEncoding(input)));
    return QUrl(url);
}
