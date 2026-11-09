#include "tab.h"

#include <QQuickWebEngineProfile>

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
    if (m_url == url)
        return;
    m_url = url;
    emit urlChanged();
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

void Tab::navigateTo(const QUrl &url)
{
    emit navigationRequested(url);
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
