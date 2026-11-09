#pragma once

#include <QAbstractListModel>
#include <QElapsedTimer>
#include <QList>
#include <QObject>
#include <QPointer>
#include <QQuickWebEngineDownloadRequest>
#include <QUrl>
#include <QWebEngineDownloadRequest>
#include <QtQmlIntegration/qqmlintegration.h>

class QQmlEngine;
class QJSEngine;

// List model behind the downloads popup. Items are the live
// QWebEngineDownloadRequest objects owned by the profiles; the model mirrors
// their state and never keeps anything on disk.
class DownloadModel : public QAbstractListModel
{
    Q_OBJECT
    QML_ANONYMOUS
    Q_PROPERTY(int count READ count NOTIFY countChanged)

public:
    enum Role {
        FileNameRole = Qt::UserRole + 1,
        DirectoryRole,
        UrlRole,
        ReceivedBytesRole,
        TotalBytesRole,
        ProgressRole,
        StateRole,
        IsPausedRole,
        IsPrivateRole,
        SpeedTextRole,
        InterruptReasonStringRole,
        MimeIconNameRole
    };
    Q_ENUM(Role)

    explicit DownloadModel(QObject *parent = nullptr);

    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role) const override;
    QHash<int, QByteArray> roleNames() const override;

    int count() const;
    bool hasActiveDownloads() const;
    // Average progress of the active downloads, or -1 when no total is known.
    qreal activeProgress() const;
    bool hasFinishedDownloads() const;

    void addDownload(QWebEngineDownloadRequest *download, bool isPrivate);
    void removeDownload(int row);
    void clearFinished();
    void removePrivateDownloads();

    QWebEngineDownloadRequest *downloadAt(int row) const;

signals:
    void countChanged();
    void activeChanged();

private:
    struct Item {
        QPointer<QWebEngineDownloadRequest> download;
        bool isPrivate = false;
        QElapsedTimer speedTimer;
        qint64 lastReceivedBytes = 0;
        qreal speed = 0;
    };

    int indexOf(const QWebEngineDownloadRequest *download) const;
    void notifyRowChanged(const QWebEngineDownloadRequest *download, const QList<int> &roles);
    void connectDownload(QWebEngineDownloadRequest *download);

    QList<Item> m_items;
};

// QML singleton `DownloadManager`: receives the profiles' download requests,
// drives the model and exposes the actions used by the downloads popup.
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
    // Mirrors QWebEngineDownloadRequest::DownloadState so QML can compare the
    // "state" role with DownloadManager.Completed and friends.
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

    // Called by ProfileManager for every profile (persistent and private).
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
    // The save dialog is open for this request; QML accepts or cancels it.
    void saveLocationRequested(QQuickWebEngineDownloadRequest *request, const QUrl &suggestedFile);
    void downloadStarted();
    void activeChanged();

private:
    explicit DownloadManager(QObject *parent = nullptr);

    DownloadModel *m_model = nullptr;
};
