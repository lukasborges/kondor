#include "downloads/downloadroles.h"

#include <QLocale>
#include <QMimeDatabase>

#include <numeric>

using State = QWebEngineDownloadRequest::DownloadState;

bool isActiveDownload(const QWebEngineDownloadRequest *download)
{
    return download && (download->state() == State::DownloadRequested
                        || download->state() == State::DownloadInProgress);
}

bool isFinishedDownload(const QWebEngineDownloadRequest *download)
{
    return download && (download->state() == State::DownloadCompleted
                        || download->state() == State::DownloadCancelled
                        || download->state() == State::DownloadInterrupted);
}

namespace {

using RoleReader = QVariant (*)(const DownloadItem &);

qreal receivedFractionOf(const QWebEngineDownloadRequest &download)
{
    const qint64 total = download.totalBytes();
    if (total <= 0)
        return -1.0;
    return static_cast<qreal>(download.receivedBytes()) / total;
}

QVariant progressOf(const DownloadItem &item)
{
    const qreal fraction = receivedFractionOf(*item.download);
    return fraction < 0.0 ? -1.0 : qMin(fraction, 1.0);
}

bool isTransferring(const DownloadItem &item)
{
    return item.download->state() == State::DownloadInProgress && !item.download->isPaused()
        && item.speed.bytesPerSecond() > 0.0;
}

QVariant speedTextOf(const DownloadItem &item)
{
    if (!isTransferring(item))
        return QString();
    return QLocale().formattedDataSize(qRound64(item.speed.bytesPerSecond())) + QStringLiteral("/s");
}

QVariant mimeIconNameOf(const DownloadItem &item)
{
    const QString mimeType = item.download->mimeType();
    const QString mimeName = mimeType.isEmpty() ? QStringLiteral("application/octet-stream") : mimeType;
    const QString iconName = QMimeDatabase().mimeTypeForName(mimeName).iconName();
    return iconName.isEmpty() ? QStringLiteral("application-octet-stream") : iconName;
}

QVariant fileNameOf(const DownloadItem &item) { return item.download->downloadFileName(); }
QVariant directoryOf(const DownloadItem &item) { return item.download->downloadDirectory(); }
QVariant urlOf(const DownloadItem &item) { return item.download->url(); }
QVariant receivedBytesOf(const DownloadItem &item) { return item.download->receivedBytes(); }
QVariant totalBytesOf(const DownloadItem &item) { return item.download->totalBytes(); }
QVariant stateOf(const DownloadItem &item) { return static_cast<int>(item.download->state()); }
QVariant isPausedOf(const DownloadItem &item) { return item.download->isPaused(); }
QVariant isPrivateOf(const DownloadItem &item) { return item.isPrivate; }
QVariant interruptReasonOf(const DownloadItem &item) { return item.download->interruptReasonString(); }

const QHash<int, RoleReader> kRoleReaders = {
    { DownloadModel::FileNameRole, fileNameOf },
    { DownloadModel::DirectoryRole, directoryOf },
    { DownloadModel::UrlRole, urlOf },
    { DownloadModel::ReceivedBytesRole, receivedBytesOf },
    { DownloadModel::TotalBytesRole, totalBytesOf },
    { DownloadModel::ProgressRole, progressOf },
    { DownloadModel::StateRole, stateOf },
    { DownloadModel::IsPausedRole, isPausedOf },
    { DownloadModel::IsPrivateRole, isPrivateOf },
    { DownloadModel::SpeedTextRole, speedTextOf },
    { DownloadModel::InterruptReasonStringRole, interruptReasonOf },
    { DownloadModel::MimeIconNameRole, mimeIconNameOf },
};

const QHash<int, QByteArray> kRoleNames = {
    { DownloadModel::FileNameRole, "fileName" },
    { DownloadModel::DirectoryRole, "directory" },
    { DownloadModel::UrlRole, "url" },
    { DownloadModel::ReceivedBytesRole, "receivedBytes" },
    { DownloadModel::TotalBytesRole, "totalBytes" },
    { DownloadModel::ProgressRole, "progress" },
    { DownloadModel::StateRole, "state" },
    { DownloadModel::IsPausedRole, "isPaused" },
    { DownloadModel::IsPrivateRole, "isPrivate" },
    { DownloadModel::SpeedTextRole, "speedText" },
    { DownloadModel::InterruptReasonStringRole, "interruptReasonString" },
    { DownloadModel::MimeIconNameRole, "mimeIconName" },
};

}

QVariant downloadRoleValue(const DownloadItem &item, int role)
{
    const RoleReader reader = kRoleReaders.value(role);
    if (!item.download || !reader)
        return {};
    return reader(item);
}

QHash<int, QByteArray> downloadRoleNames()
{
    return kRoleNames;
}

static QList<qreal> activeFractions(const QList<QWebEngineDownloadRequest *> &downloads)
{
    QList<qreal> fractions;
    for (const QWebEngineDownloadRequest *download : downloads) {
        if (isActiveDownload(download) && download->totalBytes() > 0)
            fractions.append(receivedFractionOf(*download));
    }
    return fractions;
}

qreal averageActiveProgress(const QList<QWebEngineDownloadRequest *> &downloads)
{
    const QList<qreal> fractions = activeFractions(downloads);
    if (fractions.isEmpty())
        return -1.0;
    const qreal sum = std::accumulate(fractions.begin(), fractions.end(), 0.0);
    return qBound(0.0, sum / fractions.size(), 1.0);
}

QList<QWebEngineDownloadRequest *> liveDownloadsOf(const QList<DownloadItem> &items)
{
    QList<QWebEngineDownloadRequest *> downloads;
    for (const DownloadItem &item : items) {
        if (item.download)
            downloads.append(item.download.data());
    }
    return downloads;
}
