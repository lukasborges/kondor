#pragma once

#include <QObject>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>
#include <QQuickWebEngineProfile>

class Tab : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_UNCREATABLE("Abas são criadas pelo TabModel")

    Q_PROPERTY(QString title READ title NOTIFY titleChanged)
    Q_PROPERTY(QUrl url READ url NOTIFY urlChanged)
    Q_PROPERTY(QUrl iconUrl READ iconUrl NOTIFY iconUrlChanged)
    Q_PROPERTY(qreal progress READ progress NOTIFY progressChanged)
    Q_PROPERTY(bool loading READ loading NOTIFY loadingChanged)
    Q_PROPERTY(bool canGoBack READ canGoBack NOTIFY canGoBackChanged)
    Q_PROPERTY(bool canGoForward READ canGoForward NOTIFY canGoForwardChanged)
    Q_PROPERTY(QQuickWebEngineProfile *profile READ profile CONSTANT)
    Q_PROPERTY(bool isPrivate READ isPrivate CONSTANT)

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

    // Chamadas vindas do WebEngineView (QML) para sincronizar o estado.
    Q_INVOKABLE void setTitle(const QString &title);
    Q_INVOKABLE void setUrl(const QUrl &url);
    Q_INVOKABLE void setIconUrl(const QUrl &iconUrl);
    Q_INVOKABLE void setProgress(qreal progress);
    Q_INVOKABLE void setLoading(bool loading);
    Q_INVOKABLE void setCanGoBack(bool canGoBack);
    Q_INVOKABLE void setCanGoForward(bool canGoForward);

    // Comandos vindos da interface; viram sinais consumidos pelo WebEngineView.
    Q_INVOKABLE void navigateTo(const QUrl &url);
    Q_INVOKABLE void goBack();
    Q_INVOKABLE void goForward();
    Q_INVOKABLE void reload();
    Q_INVOKABLE void stop();
    Q_INVOKABLE void zoomIn();
    Q_INVOKABLE void zoomOut();
    Q_INVOKABLE void resetZoom();

signals:
    void titleChanged();
    void urlChanged();
    void iconUrlChanged();
    void progressChanged();
    void loadingChanged();
    void canGoBackChanged();
    void canGoForwardChanged();

    void navigationRequested(const QUrl &url);
    void backRequested();
    void forwardRequested();
    void reloadRequested();
    void stopRequested();
    void zoomInRequested();
    void zoomOutRequested();
    void resetZoomRequested();

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
};
