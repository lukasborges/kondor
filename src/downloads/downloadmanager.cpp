#include "downloads/downloadmanager.h"

#include "core/notifier.h"
#include "core/settings.h"

#include <QCoreApplication>
#include <QDBusConnection>
#include <QDBusInterface>
#include <QDBusMessage>
#include <QDesktopServices>
#include <QDir>
#include <QFileInfo>
#include <QLocale>
#include <QMimeDatabase>
#include <QQuickWebEngineDownloadRequest>

DownloadModel::DownloadModel(QObject *parent)
    : QAbstractListModel(parent)
{
}

int DownloadModel::rowCount(const QModelIndex &parent) const
{
    if (parent.isValid())
        return 0;
    return m_items.size();
}

int DownloadModel::count() const
{
    return m_items.size();
}

QVariant DownloadModel::data(const QModelIndex &index, int role) const
{
    if (!index.isValid() || index.row() < 0 || index.row() >= m_items.size())
        return {};

    const Item &item = m_items.at(index.row());
    QWebEngineDownloadRequest *download = item.download.data();
    if (!download)
        return {};

    switch (role) {
    case FileNameRole:
        return download->downloadFileName();
    case DirectoryRole:
        return download->downloadDirectory();
    case UrlRole:
        return download->url();
    case ReceivedBytesRole:
        return download->receivedBytes();
    case TotalBytesRole:
        return download->totalBytes();
    case ProgressRole: {
        const qint64 total = download->totalBytes();
        if (total <= 0)
            return -1.0;
        return qBound(0.0, static_cast<qreal>(download->receivedBytes()) / total, 1.0);
    }
    case StateRole:
        return static_cast<int>(download->state());
    case IsPausedRole:
        return download->isPaused();
    case IsPrivateRole:
        return item.isPrivate;
    case SpeedTextRole: {
        // Only report a speed while data is actually flowing.
        if (download->state() != QWebEngineDownloadRequest::DownloadInProgress
            || download->isPaused() || item.speed <= 0.0) {
            return QString();
        }
        return QLocale().formattedDataSize(qRound64(item.speed)) + QStringLiteral("/s");
    }
    case InterruptReasonStringRole:
        return download->interruptReasonString();
    case MimeIconNameRole: {
        QString mimeName = download->mimeType();
        if (mimeName.isEmpty())
            mimeName = QStringLiteral("application/octet-stream");
        const QString iconName = QMimeDatabase().mimeTypeForName(mimeName).iconName();
        return iconName.isEmpty() ? QStringLiteral("application-octet-stream") : iconName;
    }
    default:
        return {};
    }
}

QHash<int, QByteArray> DownloadModel::roleNames() const
{
    return {
        { FileNameRole, "fileName" },
        { DirectoryRole, "directory" },
        { UrlRole, "url" },
        { ReceivedBytesRole, "receivedBytes" },
        { TotalBytesRole, "totalBytes" },
        { ProgressRole, "progress" },
        { StateRole, "state" },
        { IsPausedRole, "isPaused" },
        { IsPrivateRole, "isPrivate" },
        { SpeedTextRole, "speedText" },
        { InterruptReasonStringRole, "interruptReasonString" },
        { MimeIconNameRole, "mimeIconName" },
    };
}

bool DownloadModel::hasActiveDownloads() const
{
    for (const Item &item : m_items) {
        QWebEngineDownloadRequest *download = item.download.data();
        if (!download)
            continue;
        if (download->state() == QWebEngineDownloadRequest::DownloadRequested
            || download->state() == QWebEngineDownloadRequest::DownloadInProgress) {
            return true;
        }
    }
    return false;
}

qreal DownloadModel::activeProgress() const
{
    qreal sum = 0.0;
    int known = 0;
    for (const Item &item : m_items) {
        QWebEngineDownloadRequest *download = item.download.data();
        if (!download)
            continue;
        if (download->state() != QWebEngineDownloadRequest::DownloadRequested
            && download->state() != QWebEngineDownloadRequest::DownloadInProgress) {
            continue;
        }
        const qint64 total = download->totalBytes();
        if (total > 0) {
            sum += static_cast<qreal>(download->receivedBytes()) / total;
            ++known;
        }
    }
    // Any active download without a known size keeps the bar indeterminate.
    if (known == 0)
        return -1.0;
    return qBound(0.0, sum / known, 1.0);
}

bool DownloadModel::hasFinishedDownloads() const
{
    for (const Item &item : m_items) {
        QWebEngineDownloadRequest *download = item.download.data();
        if (!download)
            continue;
        if (download->state() == QWebEngineDownloadRequest::DownloadCompleted
            || download->state() == QWebEngineDownloadRequest::DownloadCancelled
            || download->state() == QWebEngineDownloadRequest::DownloadInterrupted) {
            return true;
        }
    }
    return false;
}

int DownloadModel::indexOf(const QWebEngineDownloadRequest *download) const
{
    for (int row = 0; row < m_items.size(); ++row) {
        if (m_items.at(row).download.data() == download)
            return row;
    }
    return -1;
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
    connect(download, &QWebEngineDownloadRequest::receivedBytesChanged, this, [this, download]() {
        const int row = indexOf(download);
        if (row < 0)
            return;

        Item &item = m_items[row];
        const qint64 elapsed = item.speedTimer.elapsed();
        const qint64 received = download->receivedBytes();
        if (elapsed >= 1000) {
            item.speed = static_cast<qreal>(received - item.lastReceivedBytes) * 1000.0 / elapsed;
            item.lastReceivedBytes = received;
            item.speedTimer.restart();
        }
        emit dataChanged(index(row), index(row),
                         { ReceivedBytesRole, TotalBytesRole, ProgressRole, SpeedTextRole });
        emit activeChanged();
    });

    connect(download, &QWebEngineDownloadRequest::totalBytesChanged, this, [this, download]() {
        notifyRowChanged(download, { TotalBytesRole, ProgressRole });
    });

    connect(download, &QWebEngineDownloadRequest::stateChanged, this,
            [this, download](QWebEngineDownloadRequest::DownloadState state) {
                const int row = indexOf(download);
                if (row < 0)
                    return;
                Item &item = m_items[row];
                if (state == QWebEngineDownloadRequest::DownloadInProgress && !download->isPaused()) {
                    item.speed = 0.0;
                    item.lastReceivedBytes = download->receivedBytes();
                    item.speedTimer.restart();
                } else if (state != QWebEngineDownloadRequest::DownloadInProgress) {
                    item.speed = 0.0;
                }
                emit dataChanged(index(row), index(row),
                                 { StateRole, IsPausedRole, ProgressRole, SpeedTextRole,
                                   InterruptReasonStringRole });
                emit activeChanged();
            });

    connect(download, &QWebEngineDownloadRequest::isPausedChanged, this, [this, download]() {
        const int row = indexOf(download);
        if (row < 0)
            return;
        Item &item = m_items[row];
        if (!download->isPaused()) {
            item.speed = 0.0;
            item.lastReceivedBytes = download->receivedBytes();
            item.speedTimer.restart();
        } else {
            item.speed = 0.0;
        }
        notifyRowChanged(download, { IsPausedRole, SpeedTextRole });
    });

    connect(download, &QWebEngineDownloadRequest::interruptReasonChanged, this, [this, download]() {
        notifyRowChanged(download, { InterruptReasonStringRole });
    });

    connect(download, &QWebEngineDownloadRequest::downloadFileNameChanged, this, [this, download]() {
        notifyRowChanged(download, { FileNameRole });
    });

    connect(download, &QObject::destroyed, this, [this, download]() {
        const int row = indexOf(download);
        if (row < 0)
            return;
        beginRemoveRows(QModelIndex(), row, row);
        m_items.removeAt(row);
        endRemoveRows();
        emit countChanged();
        emit activeChanged();
    });
}

void DownloadModel::addDownload(QWebEngineDownloadRequest *download, bool isPrivate)
{
    if (!download || indexOf(download) >= 0)
        return;

    Item item;
    item.download = download;
    item.isPrivate = isPrivate;
    item.lastReceivedBytes = download->receivedBytes();
    item.speedTimer.start();

    const int row = m_items.size();
    beginInsertRows(QModelIndex(), row, row);
    m_items.append(item);
    endInsertRows();
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
        QWebEngineDownloadRequest *download = m_items.at(row).download.data();
        if (!download)
            continue;
        const auto state = download->state();
        if (state == QWebEngineDownloadRequest::DownloadCompleted
            || state == QWebEngineDownloadRequest::DownloadCancelled
            || state == QWebEngineDownloadRequest::DownloadInterrupted) {
            removeDownload(row);
        }
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

DownloadManager *DownloadManager::instance()
{
    static DownloadManager *manager = new DownloadManager;
    return manager;
}

DownloadManager *DownloadManager::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(engine)
    Q_UNUSED(jsEngine)
    return instance();
}

DownloadManager::DownloadManager(QObject *parent)
    : QObject(parent)
    , m_model(new DownloadModel(this))
{
    // Private downloads live only in this session: drop them when the app quits.
    connect(QCoreApplication::instance(), &QCoreApplication::aboutToQuit,
            m_model, &DownloadModel::removePrivateDownloads);

    connect(m_model, &DownloadModel::activeChanged,
            this, &DownloadManager::activeChanged);
}

DownloadModel *DownloadManager::model() const
{
    return m_model;
}

bool DownloadManager::hasActiveDownloads() const
{
    return m_model->hasActiveDownloads();
}

qreal DownloadManager::activeProgress() const
{
    return m_model->activeProgress();
}

bool DownloadManager::hasFinishedDownloads() const
{
    return m_model->hasFinishedDownloads();
}

void DownloadManager::handleRequest(QWebEngineDownloadRequest *download, bool isPrivate)
{
    if (!download)
        return;

    // "Save Page As" already chose the file in its own dialog: keep that
    // location and do not ask again.
    const bool isSavePage = download->isSavePageDownload();
    if (!isSavePage) {
        download->setDownloadDirectory(Settings::instance()->downloadDirectory());
        if (download->downloadFileName().isEmpty())
            download->setDownloadFileName(download->suggestedFileName());
    }

    m_model->addDownload(download, isPrivate);

    connect(download, &QWebEngineDownloadRequest::stateChanged, this,
            [download](QWebEngineDownloadRequest::DownloadState state) {
                if (state == QWebEngineDownloadRequest::DownloadCompleted) {
                    Notifier::instance()->notify(tr("Download completed"),
                                                 download->downloadFileName(),
                                                 QStringLiteral("download"));
                } else if (state == QWebEngineDownloadRequest::DownloadInterrupted) {
                    QString reason = download->interruptReasonString();
                    if (reason.isEmpty())
                        reason = download->downloadFileName();
                    Notifier::instance()->notify(tr("Download failed"), reason,
                                                 QStringLiteral("download"));
                }
            });

    if (!isSavePage && Settings::instance()->askWhereToSave()) {
        auto *quickRequest = qobject_cast<QQuickWebEngineDownloadRequest *>(download);
        if (quickRequest) {
            const QString path = QDir(download->downloadDirectory())
                                     .filePath(download->downloadFileName());
            emit saveLocationRequested(quickRequest, QUrl::fromLocalFile(path));
        } else {
            // Not a QML-owned request: there is no dialog to show, so save with
            // the configured defaults instead of leaving it stuck.
            download->accept();
        }
    } else {
        download->accept();
    }

    emit downloadStarted();
}

void DownloadManager::pause(int row)
{
    if (QWebEngineDownloadRequest *download = m_model->downloadAt(row)) {
        if (download->state() == QWebEngineDownloadRequest::DownloadInProgress
            && !download->isPaused()) {
            download->pause();
        }
    }
}

void DownloadManager::resume(int row)
{
    if (QWebEngineDownloadRequest *download = m_model->downloadAt(row)) {
        if (download->state() == QWebEngineDownloadRequest::DownloadInProgress
            && download->isPaused()) {
            download->resume();
        }
    }
}

void DownloadManager::cancel(int row)
{
    if (QWebEngineDownloadRequest *download = m_model->downloadAt(row)) {
        if (download->state() == QWebEngineDownloadRequest::DownloadRequested
            || download->state() == QWebEngineDownloadRequest::DownloadInProgress) {
            download->cancel();
        }
    }
}

void DownloadManager::openFile(int row)
{
    QWebEngineDownloadRequest *download = m_model->downloadAt(row);
    if (!download || download->state() != QWebEngineDownloadRequest::DownloadCompleted)
        return;
    const QString path = QDir(download->downloadDirectory()).filePath(download->downloadFileName());
    QDesktopServices::openUrl(QUrl::fromLocalFile(path));
}

void DownloadManager::showInFolder(int row)
{
    QWebEngineDownloadRequest *download = m_model->downloadAt(row);
    if (!download)
        return;

    const QString path = QDir(download->downloadDirectory()).filePath(download->downloadFileName());
    QDBusInterface fileManager(QStringLiteral("org.freedesktop.FileManager1"),
                               QStringLiteral("/org/freedesktop/FileManager1"),
                               QStringLiteral("org.freedesktop.FileManager1"),
                               QDBusConnection::sessionBus());
    if (fileManager.isValid()) {
        const QDBusMessage reply = fileManager.call(QStringLiteral("ShowItems"),
                                                    QStringList{ QUrl::fromLocalFile(path).toString() },
                                                    QString());
        if (reply.type() != QDBusMessage::ErrorMessage)
            return;
    }

    // No file manager on D-Bus (or it failed): at least open the folder.
    QDesktopServices::openUrl(QUrl::fromLocalFile(download->downloadDirectory()));
}

void DownloadManager::removeFromList(int row)
{
    m_model->removeDownload(row);
}

void DownloadManager::clearFinished()
{
    m_model->clearFinished();
}

void DownloadManager::openDownloadsFolder()
{
    QDesktopServices::openUrl(QUrl::fromLocalFile(Settings::instance()->downloadDirectory()));
}
