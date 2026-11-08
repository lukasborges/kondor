#include "profilemanager.h"

#include <QQuickWebEngineDownloadRequest>
#include <QRegularExpression>
#include <QStandardPaths>
#include <QWebEngineDownloadRequest>

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
}

QQuickWebEngineProfile *ProfileManager::defaultProfile()
{
    if (!m_defaultProfile) {
        // Construtor com nome de storage cria um perfil persistente (on-the-record).
        m_defaultProfile = new QQuickWebEngineProfile(QStringLiteral("kondor"), this);
        m_defaultProfile->setPersistentCookiesPolicy(QQuickWebEngineProfile::AllowPersistentCookies);
        setupProfile(m_defaultProfile);
    }
    return m_defaultProfile;
}

QQuickWebEngineProfile *ProfileManager::createPrivateProfile()
{
    // Sem nome de storage: perfil off-the-record (privado), isolado.
    auto *profile = new QQuickWebEngineProfile(this);
    profile->setPersistentCookiesPolicy(QQuickWebEngineProfile::NoPersistentCookies);
    setupProfile(profile);
    return profile;
}

void ProfileManager::setupProfile(QQuickWebEngineProfile *profile)
{
    // User-Agent: mantém o Chromium (compatibilidade), mas remove o token
    // "QtWebEngine", que faz alguns sites tratarem o navegador como desconhecido.
    QString userAgent = profile->httpUserAgent();
    static const QRegularExpression qtWebEngineToken(QStringLiteral("QtWebEngine/[^ ]+"));
    userAgent.replace(qtWebEngineToken, QStringLiteral("Kondor/0.1"));
    profile->setHttpUserAgent(userAgent);

    // Download básico: salva em ~/Downloads.
    connect(profile, &QQuickWebEngineProfile::downloadRequested, this,
            [](QWebEngineDownloadRequest *download) {
                download->setDownloadDirectory(
                    QStandardPaths::writableLocation(QStandardPaths::DownloadLocation));
                download->accept();
            });
}

QUrl ProfileManager::resolveAddress(const QString &text) const
{
    const QString input = text.trimmed();
    if (input.isEmpty())
        return QUrl(m_homePage);

    if (input.contains(QLatin1String("://"))
        || input.startsWith(QLatin1String("about:"))
        || input.startsWith(QLatin1String("data:"))) {
        return QUrl::fromUserInput(input);
    }

    // IP, localhost ou domínio com TLD -> assume https.
    static const QRegularExpression hostRe(QStringLiteral(
        R"(^(([0-9]{1,3}\.){3}[0-9]{1,3}|localhost|[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})(:\d+)?(/.*)?$)"));
    if (hostRe.match(input).hasMatch())
        return QUrl(QStringLiteral("https://") + input);

    // Senão, pesquisa no motor configurado.
    QString url = m_searchEngineUrl;
    url.replace(QLatin1String("%1"), QString::fromUtf8(QUrl::toPercentEncoding(input)));
    return QUrl(url);
}

void ProfileManager::setSearchEngineUrl(const QString &url)
{
    if (m_searchEngineUrl == url)
        return;
    m_searchEngineUrl = url;
    emit searchEngineUrlChanged();
}
