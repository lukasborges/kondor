#pragma once

#include "downloads/downloadmodel.h"

#include <QObject>
#include <QQuickWebEngineDownloadRequest>
#include <QUrl>
#include <QWebEngineDownloadRequest>
#include <QtQmlIntegration/qqmlintegration.h>

class QQmlEngine;
class QJSEngine;

class DownloadManager : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    Q_PROPERTY(DownloadModel *model READ model CONSTANT)
    Q_PROPERTY(bool hasActiveDownloads READ hasActiveDownloads NOTIFY activeChanged)
    Q_PROPERTY(qreal activeProgress READ activeProgress NOTIFY activeChanged)
    Q_PROPERTY(bool hasFinishedDownloads READ hasFinishedDownloads NOTIFY activeChanged)

public:
    enum State {
        Requested = QWebEngineDownloadRequest::DownloadRequested,
        InProgress = QWebEngineDownloadRequest::DownloadInProgress,
        Completed = QWebEngineDownloadRequest::DownloadCompleted,
        Cancelled = QWebEngineDownloadRequest::DownloadCancelled,
        Interrupted = QWebEngineDownloadRequest::DownloadInterrupted
    };
    Q_ENUM(State)

    static DownloadManager *instance();
    static DownloadManager *create(QQmlEngine *engine, QJSEngine *jsEngine);

    DownloadModel *model() const;
    bool hasActiveDownloads() const;
    qreal activeProgress() const;
    bool hasFinishedDownloads() const;

    void handleRequest(QWebEngineDownloadRequest *download, bool isPrivate = false);

    Q_INVOKABLE void pause(int row);
    Q_INVOKABLE void resume(int row);
    Q_INVOKABLE void cancel(int row);
    Q_INVOKABLE void openFile(int row);
    Q_INVOKABLE void showInFolder(int row);
    Q_INVOKABLE void removeFromList(int row);
    Q_INVOKABLE void clearFinished();
    Q_INVOKABLE void openDownloadsFolder();

signals:
    void saveLocationRequested(QQuickWebEngineDownloadRequest *request, const QUrl &suggestedFile);
    void downloadStarted();
    void activeChanged();

private:
    explicit DownloadManager(QObject *parent = nullptr);

    void acceptOrAsk(QWebEngineDownloadRequest *download);
    void requestSaveLocation(QWebEngineDownloadRequest *download);
    void connectNotifications(QWebEngineDownloadRequest *download);
    void notifyCompleted(const QWebEngineDownloadRequest *download);
    void notifyFailed(const QWebEngineDownloadRequest *download);

    DownloadModel *m_model = nullptr;
};
