#include "tab.h"

#include "profilemanager.h"

#include <QQuickWebEngineProfile>

#include <utility>

namespace {
bool sameOrigin(const QUrl &a, const QUrl &b)
{
    if (a.isEmpty() || b.isEmpty())
        return false;
    return a.scheme().compare(b.scheme(), Qt::CaseInsensitive) == 0
            && a.host().compare(b.host(), Qt::CaseInsensitive) == 0 && a.port() == b.port();
}
}

Tab::Tab(QQuickWebEngineProfile *profile, QObject *parent)
    : QObject(parent)
    , m_profile(profile)
    , m_isPrivate(profile && profile->isOffTheRecord())
{
}

void Tab::setTitle(const QString &title)
{
    if (m_title == title)
        return;
    m_title = title;
    emit titleChanged();
}

void Tab::setUrl(const QUrl &url)
{
    // about:blank is what showNewTabPage() loads, so the native page stays on
    // screen; any other non-empty URL means the tab shows a real page again.
    if (!url.isEmpty() && url != QUrl(QStringLiteral("about:blank")))
        setNewTabPage(false);

    // A prompt belongs to the origin that asked; leaving it denies the request.
    // Same-document changes (fragment, history.pushState) and same-origin
    // navigations keep it, so single-page apps like Meet keep their prompts.
    if (!sameOrigin(m_url, url))
        denyPendingPermissions();

    if (m_url == url)
        return;
    m_url = url;
    updateSecurityState();
    emit urlChanged();
}

void Tab::updateSecurityState()
{
    QString state;
    const QString scheme = m_url.scheme().toLower();
    if (m_certificateErrorPending) {
        // While the warning is on screen the indicator must match it.
        state = QStringLiteral("error");
    } else if (scheme == QLatin1String("https")) {
        // Qt WebEngine accepts an overridden host's certificate for the whole
        // lifetime of the profile without asking again, so the set kept by
        // ProfileManager decides the state, not this tab's history.
        const bool overridden = ProfileManager::instance()->isCertificateOverridden(m_profile,
                                                                                    m_url.host());
        state = overridden ? QStringLiteral("error") : QStringLiteral("secure");
    } else if (scheme == QLatin1String("http")) {
        state = QStringLiteral("insecure");
    } else {
        state = QStringLiteral("local");
    }

    if (m_securityState == state)
        return;
    m_securityState = state;
    emit securityStateChanged();
}

void Tab::setPendingCertificateError(const QUrl &url, const QString &description, bool overridable)
{
    if (m_certificateErrorPending && m_certificateErrorUrl == url
            && m_certificateErrorDescription == description
            && m_certificateErrorOverridable == overridable) {
        return;
    }

    m_certificateErrorPending = true;
    m_certificateErrorUrl = url;
    m_certificateErrorDescription = description;
    m_certificateErrorOverridable = overridable;
    updateSecurityState();
    emit certificateErrorChanged();
}

void Tab::clearPendingCertificateError()
{
    if (!m_certificateErrorPending)
        return;
    m_certificateErrorPending = false;
    m_certificateErrorUrl.clear();
    m_certificateErrorDescription.clear();
    m_certificateErrorOverridable = false;
    updateSecurityState();
    emit certificateErrorChanged();
}

void Tab::markCertificateOverridden()
{
    QString host = m_certificateErrorUrl.host();
    if (host.isEmpty())
        host = m_url.host();
    ProfileManager::instance()->markCertificateOverridden(m_profile, host);
}

void Tab::acceptCertificateError()
{
    if (!m_certificateErrorPending)
        return;
    markCertificateOverridden();
    clearPendingCertificateError();
    emit acceptCertificateErrorRequested();
}

void Tab::rejectCertificateError()
{
    if (!m_certificateErrorPending)
        return;
    clearPendingCertificateError();
    emit rejectCertificateErrorRequested();
}

void Tab::setIconUrl(const QUrl &iconUrl)
{
    if (m_iconUrl == iconUrl)
        return;
    m_iconUrl = iconUrl;
    emit iconUrlChanged();
}

void Tab::setProgress(qreal progress)
{
    if (qFuzzyCompare(m_progress, progress))
        return;
    m_progress = progress;
    emit progressChanged();
}

void Tab::setLoading(bool loading)
{
    if (m_loading == loading)
        return;
    m_loading = loading;
    emit loadingChanged();
}

void Tab::setCanGoBack(bool canGoBack)
{
    if (m_canGoBack == canGoBack)
        return;
    m_canGoBack = canGoBack;
    emit canGoBackChanged();
}

void Tab::setCanGoForward(bool canGoForward)
{
    if (m_canGoForward == canGoForward)
        return;
    m_canGoForward = canGoForward;
    emit canGoForwardChanged();
}

void Tab::setFindResult(int matches, int activeMatch)
{
    if (m_findMatches == matches && m_findActiveMatch == activeMatch)
        return;
    m_findMatches = matches;
    m_findActiveMatch = activeMatch;
    emit findResultChanged();
}

void Tab::setPinned(bool pinned)
{
    if (m_pinned == pinned)
        return;
    m_pinned = pinned;
    emit pinnedChanged();
}

void Tab::setNewTabPage(bool newTabPage)
{
    if (m_newTabPage == newTabPage)
        return;
    m_newTabPage = newTabPage;
    emit newTabPageChanged();
}

void Tab::navigateTo(const QUrl &url)
{
    // An empty URL means the New Tab page, which no caller navigates to.
    if (url.isEmpty())
        return;
    // Typing another address while the certificate warning is up abandons the
    // pending request; the view rejects it before navigating.
    clearPendingCertificateError();
    setNewTabPage(false);
    emit navigationRequested(url);
}

void Tab::showNewTabPage()
{
    // Already there: loading about:blank again would add a useless entry to the
    // page history and make Back stay on the same blank page.
    if (m_newTabPage)
        return;
    clearPendingCertificateError();
    setNewTabPage(true);
    emit newTabPageRequested();
}

void Tab::goBack()
{
    emit backRequested();
}

void Tab::goForward()
{
    emit forwardRequested();
}

void Tab::reload()
{
    emit reloadRequested();
}

void Tab::stop()
{
    emit stopRequested();
}

void Tab::zoomIn()
{
    emit zoomInRequested();
}

void Tab::zoomOut()
{
    emit zoomOutRequested();
}

void Tab::resetZoom()
{
    emit resetZoomRequested();
}

void Tab::find(const QString &text, bool backward, bool caseSensitive)
{
    emit findRequested(text, backward, caseSensitive);
}

void Tab::stopFind()
{
    emit stopFindRequested();
}

void Tab::focusPage()
{
    emit focusPageRequested();
}

QVariant Tab::pendingPermission() const
{
    if (m_pendingPermissions.isEmpty())
        return QVariant();
    return QVariant::fromValue(m_pendingPermissions.first());
}

void Tab::enqueuePermission(const QWebEnginePermission &permission)
{
    if (!permission.isValid())
        return;

    const bool wasEmpty = m_pendingPermissions.isEmpty();
    m_pendingPermissions.append(permission);
    if (wasEmpty)
        emit pendingPermissionChanged();
}

void Tab::answerPermission(bool grant)
{
    bool changed = false;
    while (!m_pendingPermissions.isEmpty() && !m_pendingPermissions.first().isValid()) {
        m_pendingPermissions.removeFirst();
        changed = true;
    }

    if (m_pendingPermissions.isEmpty()) {
        if (changed)
            emit pendingPermissionChanged();
        return;
    }

    const QWebEnginePermission permission = m_pendingPermissions.takeFirst();
    if (grant)
        permission.grant();
    else
        permission.deny();
    emit pendingPermissionChanged();
}

void Tab::denyPendingPermissions()
{
    if (m_pendingPermissions.isEmpty())
        return;

    for (const QWebEnginePermission &permission : std::as_const(m_pendingPermissions)) {
        if (permission.isValid())
            permission.deny();
    }
    m_pendingPermissions.clear();
    emit pendingPermissionChanged();
}
