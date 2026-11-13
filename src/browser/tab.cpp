#include "browser/tab.h"

#include "browser/assignandnotify.h"

#include <QQuickWebEngineProfile>

namespace {
bool sameOrigin(const QUrl &first, const QUrl &second)
{
    if (first.isEmpty() || second.isEmpty())
        return false;
    return first.scheme().compare(second.scheme(), Qt::CaseInsensitive) == 0
            && first.host().compare(second.host(), Qt::CaseInsensitive) == 0
            && first.port() == second.port();
}

bool isRealPage(const QUrl &url)
{
    return !url.isEmpty() && url != QUrl(QStringLiteral("about:blank"));
}
}

Tab::Tab(QQuickWebEngineProfile *profile, QObject *parent)
    : QObject(parent)
    , m_profile(profile)
    , m_isPrivate(profile && profile->isOffTheRecord())
    , m_security(new TabSecurity(profile, this))
    , m_permissions(new TabPermissions(this))
    , m_passwords(new TabPasswords(m_isPrivate, this))
    , m_siteReload(new TabSiteReload(this))
    , m_extensionItems(new TabExtensionItems(this))
{
}

void Tab::setTitle(const QString &title)
{
    assignAndNotify(m_title, title, [this] { emit titleChanged(); });
}

void Tab::denyAndDismissSiteState()
{
    m_permissions->denyAll();
    m_siteReload->dismiss();
}

void Tab::setUrl(const QUrl &url)
{
    if (isRealPage(url))
        setNewTabPage(false);
    if (!sameOrigin(m_url, url))
        denyAndDismissSiteState();
    if (m_url == url)
        return;
    m_url = url;
    m_security->updateFor(url);
    m_passwords->updateUsernamesFor(url);
    emit urlChanged();
}

void Tab::setIconUrl(const QUrl &iconUrl)
{
    assignAndNotify(m_iconUrl, iconUrl, [this] { emit iconUrlChanged(); });
}

void Tab::setProgress(qreal progress)
{
    assignAndNotify(m_progress, progress, [this] { emit progressChanged(); });
}

void Tab::setLoading(bool loading)
{
    assignAndNotify(m_loading, loading, [this] { emit loadingChanged(); });
}

void Tab::setCanGoBack(bool canGoBack)
{
    assignAndNotify(m_canGoBack, canGoBack, [this] { emit canGoBackChanged(); });
}

void Tab::setCanGoForward(bool canGoForward)
{
    assignAndNotify(m_canGoForward, canGoForward, [this] { emit canGoForwardChanged(); });
}

void Tab::setZoomFactor(qreal factor)
{
    assignAndNotify(m_zoomFactor, factor, [this] { emit zoomFactorChanged(); });
}

void Tab::setPinned(bool pinned)
{
    assignAndNotify(m_pinned, pinned, [this] { emit pinnedChanged(); });
}

void Tab::setFullScreen(bool fullScreen)
{
    assignAndNotify(m_isFullScreen, fullScreen, [this] { emit fullScreenChanged(); });
}

void Tab::setDevToolsOpen(bool open)
{
    assignAndNotify(m_devToolsOpen, open, [this] { emit devToolsOpenChanged(); });
}

void Tab::setReaderAvailable(bool available)
{
    assignAndNotify(m_readerAvailable, available, [this] { emit readerAvailableChanged(); });
}

void Tab::setReaderActive(bool active)
{
    assignAndNotify(m_readerActive, active, [this] { emit readerActiveChanged(); });
}

void Tab::setNewTabPage(bool newTabPage)
{
    assignAndNotify(m_newTabPage, newTabPage, [this] { emit newTabPageChanged(); });
}

void Tab::setFindResult(int matches, int activeMatch)
{
    if (m_findMatches == matches && m_findActiveMatch == activeMatch)
        return;
    m_findMatches = matches;
    m_findActiveMatch = activeMatch;
    emit findResultChanged();
}

void Tab::setCrashed(bool crashed, const QString &reason, int exitCode)
{
    if (m_crashed == crashed && m_crashReason == reason && m_crashExitCode == exitCode)
        return;
    m_crashed = crashed;
    m_crashReason = crashed ? reason : QString();
    m_crashExitCode = crashed ? exitCode : 0;
    emit crashChanged();
}

void Tab::navigateTo(const QUrl &url)
{
    if (url.isEmpty())
        return;
    m_security->clearPendingCertificateError();
    setNewTabPage(false);
    emit navigationRequested(url);
}

void Tab::showNewTabPage()
{
    if (m_newTabPage)
        return;
    m_security->clearPendingCertificateError();
    setNewTabPage(true);
    emit newTabPageRequested();
}

void Tab::exitFullScreen()
{
    if (m_isFullScreen)
        emit exitFullScreenRequested();
}

void Tab::toggleReaderMode()
{
    if (m_readerAvailable || m_readerActive)
        emit toggleReaderModeRequested();
}
