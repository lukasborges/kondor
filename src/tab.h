#pragma once

#include <QObject>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>
#include <QQuickWebEngineProfile>

class Tab : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_UNCREATABLE("Tabs are created by TabModel")

    Q_PROPERTY(QString title READ title NOTIFY titleChanged)
    Q_PROPERTY(QUrl url READ url NOTIFY urlChanged)
    Q_PROPERTY(QUrl iconUrl READ iconUrl NOTIFY iconUrlChanged)
    Q_PROPERTY(qreal progress READ progress NOTIFY progressChanged)
    Q_PROPERTY(bool loading READ loading NOTIFY loadingChanged)
    Q_PROPERTY(bool canGoBack READ canGoBack NOTIFY canGoBackChanged)
    Q_PROPERTY(bool canGoForward READ canGoForward NOTIFY canGoForwardChanged)
    Q_PROPERTY(QQuickWebEngineProfile *profile READ profile CONSTANT)
    Q_PROPERTY(bool isPrivate READ isPrivate CONSTANT)
    Q_PROPERTY(bool pinned READ pinned NOTIFY pinnedChanged)
    Q_PROPERTY(int findMatches READ findMatches NOTIFY findResultChanged)
    Q_PROPERTY(int findActiveMatch READ findActiveMatch NOTIFY findResultChanged)

public:
    explicit Tab(QQuickWebEngineProfile *profile, QObject *parent = nullptr);

    QString title() const { return m_title; }
    QUrl url() const { return m_url; }
    QUrl iconUrl() const { return m_iconUrl; }
    qreal progress() const { return m_progress; }
    bool loading() const { return m_loading; }
    bool canGoBack() const { return m_canGoBack; }
    bool canGoForward() const { return m_canGoForward; }
    QQuickWebEngineProfile *profile() const { return m_profile; }
    bool isPrivate() const { return m_isPrivate; }
    bool pinned() const { return m_pinned; }
    int findMatches() const { return m_findMatches; }
    int findActiveMatch() const { return m_findActiveMatch; }

    // Calls coming from the WebEngineView (QML) to synchronize the state.
    Q_INVOKABLE void setTitle(const QString &title);
    Q_INVOKABLE void setUrl(const QUrl &url);
    Q_INVOKABLE void setIconUrl(const QUrl &iconUrl);
    Q_INVOKABLE void setProgress(qreal progress);
    Q_INVOKABLE void setLoading(bool loading);
    Q_INVOKABLE void setCanGoBack(bool canGoBack);
    Q_INVOKABLE void setCanGoForward(bool canGoForward);
    Q_INVOKABLE void setFindResult(int matches, int activeMatch);
    void setPinned(bool pinned);

    // Commands coming from the UI; they become signals consumed by the WebEngineView.
    Q_INVOKABLE void navigateTo(const QUrl &url);
    Q_INVOKABLE void goBack();
    Q_INVOKABLE void goForward();
    Q_INVOKABLE void reload();
    Q_INVOKABLE void stop();
    Q_INVOKABLE void zoomIn();
    Q_INVOKABLE void zoomOut();
    Q_INVOKABLE void resetZoom();
    Q_INVOKABLE void find(const QString &text, bool backward, bool caseSensitive);
    Q_INVOKABLE void stopFind();

signals:
    void titleChanged();
    void urlChanged();
    void iconUrlChanged();
    void progressChanged();
    void loadingChanged();
    void canGoBackChanged();
    void canGoForwardChanged();
    void findResultChanged();
    void pinnedChanged();

    void navigationRequested(const QUrl &url);
    void backRequested();
    void forwardRequested();
    void reloadRequested();
    void stopRequested();
    void zoomInRequested();
    void zoomOutRequested();
    void resetZoomRequested();
    void findRequested(const QString &text, bool backward, bool caseSensitive);
    void stopFindRequested();

private:
    QString m_title;
    QUrl m_url;
    QUrl m_iconUrl;
    qreal m_progress = 0.0;
    bool m_loading = false;
    bool m_canGoBack = false;
    bool m_canGoForward = false;
    QQuickWebEngineProfile *m_profile = nullptr;
    bool m_isPrivate = false;
    bool m_pinned = false;
    int m_findMatches = 0;
    int m_findActiveMatch = 0;
};
