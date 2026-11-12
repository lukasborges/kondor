#pragma once

#include "downloads/transferspeed.h"

#include <QAbstractListModel>
#include <QList>
#include <QPointer>
#include <QWebEngineDownloadRequest>
#include <QtQmlIntegration/qqmlintegration.h>

struct DownloadItem {
    QPointer<QWebEngineDownloadRequest> download;
    bool isPrivate = false;
    TransferSpeed speed;
};

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
    int indexOf(const QWebEngineDownloadRequest *download) const;
    DownloadItem *itemOf(const QWebEngineDownloadRequest *download);
    void notifyRowChanged(const QWebEngineDownloadRequest *download, const QList<int> &roles);
    void appendItem(QWebEngineDownloadRequest *download, bool isPrivate);
    void connectDownload(QWebEngineDownloadRequest *download);
    void connectProgressSignals(QWebEngineDownloadRequest *download);
    void connectStateSignals(QWebEngineDownloadRequest *download);
    void onReceivedBytesChanged(QWebEngineDownloadRequest *download);
    void onStateChanged(QWebEngineDownloadRequest *download);
    void onPausedChanged(QWebEngineDownloadRequest *download);
    void onDownloadDestroyed(QWebEngineDownloadRequest *download);

    QList<DownloadItem> m_items;
};
