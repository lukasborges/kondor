#pragma once

#include <QObject>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>

#include "browser/tabextensionitems.h"
#include "browser/tabpasswords.h"
#include "browser/tabpermissions.h"
#include "browser/tabsecurity.h"

class QQuickWebEngineProfile;

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
    Q_PROPERTY(qreal zoomFactor READ zoomFactor NOTIFY zoomFactorChanged)
    Q_PROPERTY(bool isPrivate READ isPrivate CONSTANT)
    Q_PROPERTY(bool pinned READ pinned NOTIFY pinnedChanged)
    Q_PROPERTY(int findMatches READ findMatches NOTIFY findResultChanged)
    Q_PROPERTY(int findActiveMatch READ findActiveMatch NOTIFY findResultChanged)
    Q_PROPERTY(bool newTabPage READ newTabPage NOTIFY newTabPageChanged)
    Q_PROPERTY(bool isFullScreen READ isFullScreen NOTIFY fullScreenChanged)
    Q_PROPERTY(bool devToolsOpen READ devToolsOpen NOTIFY devToolsOpenChanged)
    Q_PROPERTY(bool readerAvailable READ readerAvailable NOTIFY readerAvailableChanged)
    Q_PROPERTY(bool readerActive READ readerActive NOTIFY readerActiveChanged)
    Q_PROPERTY(bool crashed READ crashed NOTIFY crashChanged)
    Q_PROPERTY(QString crashReason READ crashReason NOTIFY crashChanged)
    Q_PROPERTY(int crashExitCode READ crashExitCode NOTIFY crashChanged)
    Q_PROPERTY(TabSecurity *security READ security CONSTANT)
    Q_PROPERTY(TabPermissions *permissions READ permissions CONSTANT)
    Q_PROPERTY(TabPasswords *passwords READ passwords CONSTANT)
    Q_PROPERTY(TabExtensionItems *extensionItems READ extensionItems CONSTANT)

public:
    explicit Tab(QQuickWebEngineProfile *profile, QObject *parent = nullptr);

    QString title() const { return m_title; }
    QUrl url() const { return m_url; }
    qreal zoomFactor() const { return m_zoomFactor; }
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
    bool newTabPage() const { return m_newTabPage; }
    bool isFullScreen() const { return m_isFullScreen; }
    bool devToolsOpen() const { return m_devToolsOpen; }
    bool readerAvailable() const { return m_readerAvailable; }
    bool readerActive() const { return m_readerActive; }
    bool crashed() const { return m_crashed; }
    QString crashReason() const { return m_crashReason; }
    int crashExitCode() const { return m_crashExitCode; }
    TabSecurity *security() const { return m_security; }
    TabPermissions *permissions() const { return m_permissions; }
    TabPasswords *passwords() const { return m_passwords; }
    TabExtensionItems *extensionItems() const { return m_extensionItems; }

    Q_INVOKABLE void setTitle(const QString &title);
    Q_INVOKABLE void setUrl(const QUrl &url);
    Q_INVOKABLE void setZoomFactor(qreal factor);
    Q_INVOKABLE void setIconUrl(const QUrl &iconUrl);
    Q_INVOKABLE void setProgress(qreal progress);
    Q_INVOKABLE void setLoading(bool loading);
    Q_INVOKABLE void setCanGoBack(bool canGoBack);
    Q_INVOKABLE void setCanGoForward(bool canGoForward);
    Q_INVOKABLE void setFindResult(int matches, int activeMatch);
    Q_INVOKABLE void setFullScreen(bool fullScreen);
    Q_INVOKABLE void setCrashed(bool crashed, const QString &reason = QString(),
                                int exitCode = 0);
    Q_INVOKABLE void setDevToolsOpen(bool open);
    Q_INVOKABLE void setReaderAvailable(bool available);
    Q_INVOKABLE void setReaderActive(bool active);
    Q_INVOKABLE void setPdfFinished(const QString &filePath, bool success);
    void setPinned(bool pinned);

    Q_INVOKABLE void navigateTo(const QUrl &url);
    Q_INVOKABLE void showNewTabPage();
    Q_INVOKABLE void goBack();
    Q_INVOKABLE void goForward();
    Q_INVOKABLE void reload();
    Q_INVOKABLE void stop();
    Q_INVOKABLE void zoomIn();
    Q_INVOKABLE void zoomOut();
    Q_INVOKABLE void resetZoom();
    Q_INVOKABLE void find(const QString &text, bool backward, bool caseSensitive);
    Q_INVOKABLE void stopFind();
    Q_INVOKABLE void focusPage();
    Q_INVOKABLE void exitFullScreen();
    Q_INVOKABLE void toggleDevTools();
    Q_INVOKABLE void toggleReaderMode();
    Q_INVOKABLE void printToPdf(const QString &filePath);
    Q_INVOKABLE void print();
    Q_INVOKABLE void savePage(const QString &filePath, int format);
    Q_INVOKABLE void inspectElement();
    Q_INVOKABLE void closeTab();
    Q_INVOKABLE void openTab(const QUrl &url, bool background);
    Q_INVOKABLE void selectNeighborTab(int delta);
    Q_INVOKABLE void downloadUrl(const QUrl &url, const QString &fileName);

signals:
    void titleChanged();
    void urlChanged();
    void zoomFactorChanged();
    void iconUrlChanged();
    void progressChanged();
    void loadingChanged();
    void canGoBackChanged();
    void canGoForwardChanged();
    void findResultChanged();
    void pinnedChanged();
    void newTabPageChanged();
    void fullScreenChanged();
    void devToolsOpenChanged();
    void readerAvailableChanged();
    void readerActiveChanged();
    void crashChanged();

    void navigationRequested(const QUrl &url);
    void newTabPageRequested();
    void backRequested();
    void forwardRequested();
    void reloadRequested();
    void stopRequested();
    void zoomInRequested();
    void zoomOutRequested();
    void resetZoomRequested();
    void findRequested(const QString &text, bool backward, bool caseSensitive);
    void stopFindRequested();
    void focusPageRequested();
    void exitFullScreenRequested();
    void toggleDevToolsRequested();
    void toggleReaderModeRequested();
    void printToPdfRequested(const QString &filePath);
    void printRequested();
    void savePageRequested(const QString &filePath, int format);
    void pdfFinished(const QString &filePath, bool success);
    void inspectElementRequested();
    void closeRequested();
    void openTabRequested(const QUrl &url, bool background);
    void neighborTabRequested(int delta);
    void downloadUrlRequested(const QUrl &url, const QString &fileName);

private:
    void setNewTabPage(bool newTabPage);

    QString m_title;
    QUrl m_url;
    qreal m_zoomFactor = 1.0;
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
    bool m_newTabPage = true;
    bool m_isFullScreen = false;
    bool m_devToolsOpen = false;
    bool m_readerAvailable = false;
    bool m_readerActive = false;
    bool m_crashed = false;
    QString m_crashReason;
    int m_crashExitCode = 0;
    TabSecurity *m_security = nullptr;
    TabPermissions *m_permissions = nullptr;
    TabPasswords *m_passwords = nullptr;
    TabExtensionItems *m_extensionItems = nullptr;
};
