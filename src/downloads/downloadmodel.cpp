#include "downloads/downloadmodel.h"

#include "downloads/downloadroles.h"

#include <algorithm>

using State = QWebEngineDownloadRequest::DownloadState;

DownloadModel::DownloadModel(QObject *parent)
    : QAbstractListModel(parent)
{
}

int DownloadModel::rowCount(const QModelIndex &parent) const
{
    return parent.isValid() ? 0 : m_items.size();
}

int DownloadModel::count() const
{
    return m_items.size();
}

QVariant DownloadModel::data(const QModelIndex &index, int role) const
{
    if (!index.isValid() || index.row() >= m_items.size())
        return {};
    const DownloadItem &item = m_items.at(index.row());
    return downloadRoleValue(item, role);
}

QHash<int, QByteArray> DownloadModel::roleNames() const
{
    return downloadRoleNames();
}

bool DownloadModel::hasActiveDownloads() const
{
    const auto downloads = liveDownloadsOf(m_items);
    return std::any_of(downloads.begin(), downloads.end(), isActiveDownload);
}

bool DownloadModel::hasFinishedDownloads() const
{
    const auto downloads = liveDownloadsOf(m_items);
    return std::any_of(downloads.begin(), downloads.end(), isFinishedDownload);
}

qreal DownloadModel::activeProgress() const
{
    return averageActiveProgress(liveDownloadsOf(m_items));
}

int DownloadModel::indexOf(const QWebEngineDownloadRequest *download) const
{
    for (int row = 0; row < m_items.size(); ++row) {
        if (m_items.at(row).download.data() == download)
            return row;
    }
    return -1;
}

DownloadItem *DownloadModel::itemOf(const QWebEngineDownloadRequest *download)
{
    const int row = indexOf(download);
    return row < 0 ? nullptr : &m_items[row];
}

void DownloadModel::notifyRowChanged(const QWebEngineDownloadRequest *download, const QList<int> &roles)
{
    const int row = indexOf(download);
    if (row < 0)
        return;
    emit dataChanged(index(row), index(row), roles);
    emit activeChanged();
}

void DownloadModel::connectDownload(QWebEngineDownloadRequest *download)
{
    connectProgressSignals(download);
    connectStateSignals(download);
    connect(download, &QObject::destroyed, this, [this, download] { onDownloadDestroyed(download); });
}

void DownloadModel::connectProgressSignals(QWebEngineDownloadRequest *download)
{
    using Request = QWebEngineDownloadRequest;
    connect(download, &Request::receivedBytesChanged, this,
            [this, download] { onReceivedBytesChanged(download); });
    connect(download, &Request::totalBytesChanged, this,
            [this, download] { notifyRowChanged(download, { TotalBytesRole, ProgressRole }); });
    connect(download, &Request::downloadFileNameChanged, this,
            [this, download] { notifyRowChanged(download, { FileNameRole }); });
}

void DownloadModel::connectStateSignals(QWebEngineDownloadRequest *download)
{
    using Request = QWebEngineDownloadRequest;
    connect(download, &Request::stateChanged, this, [this, download] { onStateChanged(download); });
    connect(download, &Request::isPausedChanged, this, [this, download] { onPausedChanged(download); });
    connect(download, &Request::interruptReasonChanged, this,
            [this, download] { notifyRowChanged(download, { InterruptReasonStringRole }); });
}

void DownloadModel::onReceivedBytesChanged(QWebEngineDownloadRequest *download)
{
    DownloadItem *item = itemOf(download);
    if (!item)
        return;
    item->speed.update(download->receivedBytes());
    notifyRowChanged(download, { ReceivedBytesRole, TotalBytesRole, ProgressRole, SpeedTextRole });
}

void DownloadModel::onStateChanged(QWebEngineDownloadRequest *download)
{
    DownloadItem *item = itemOf(download);
    if (!item)
        return;
    if (download->state() != State::DownloadInProgress)
        item->speed.stop();
    else if (!download->isPaused())
        item->speed.restart(download->receivedBytes());
    notifyRowChanged(download, { StateRole, IsPausedRole, ProgressRole, SpeedTextRole,
                                 InterruptReasonStringRole });
}

void DownloadModel::onPausedChanged(QWebEngineDownloadRequest *download)
{
    DownloadItem *item = itemOf(download);
    if (!item)
        return;
    if (download->isPaused())
        item->speed.stop();
    else
        item->speed.restart(download->receivedBytes());
    notifyRowChanged(download, { IsPausedRole, SpeedTextRole });
}

void DownloadModel::onDownloadDestroyed(QWebEngineDownloadRequest *download)
{
    removeDownload(indexOf(download));
}

void DownloadModel::appendItem(QWebEngineDownloadRequest *download, bool isPrivate)
{
    DownloadItem item;
    item.download = download;
    item.isPrivate = isPrivate;
    item.speed.restart(download->receivedBytes());
    beginInsertRows(QModelIndex(), m_items.size(), m_items.size());
    m_items.append(item);
    endInsertRows();
}

void DownloadModel::addDownload(QWebEngineDownloadRequest *download, bool isPrivate)
{
    if (!download || indexOf(download) >= 0)
        return;
    appendItem(download, isPrivate);
    connectDownload(download);
    emit countChanged();
    emit activeChanged();
}

void DownloadModel::removeDownload(int row)
{
    if (row < 0 || row >= m_items.size())
        return;
    beginRemoveRows(QModelIndex(), row, row);
    m_items.removeAt(row);
    endRemoveRows();
    emit countChanged();
    emit activeChanged();
}

void DownloadModel::clearFinished()
{
    for (int row = m_items.size() - 1; row >= 0; --row) {
        if (isFinishedDownload(m_items.at(row).download.data()))
            removeDownload(row);
    }
}

void DownloadModel::removePrivateDownloads()
{
    for (int row = m_items.size() - 1; row >= 0; --row) {
        if (m_items.at(row).isPrivate)
            removeDownload(row);
    }
}

QWebEngineDownloadRequest *DownloadModel::downloadAt(int row) const
{
    if (row < 0 || row >= m_items.size())
        return nullptr;
    return m_items.at(row).download.data();
}
