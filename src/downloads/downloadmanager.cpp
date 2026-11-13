#include "downloads/downloadmanager.h"

#include "core/notifier.h"
#include "core/settings/settings.h"
#include "downloads/downloadroles.h"

#include <QCoreApplication>
#include <QDBusConnection>
#include <QDBusInterface>
#include <QDBusMessage>
#include <QDesktopServices>
#include <QDir>

namespace {

const QString kFileManagerService = QStringLiteral("org.freedesktop.FileManager1");
const QString kFileManagerPath = QStringLiteral("/org/freedesktop/FileManager1");

QString targetPathOf(const QWebEngineDownloadRequest *download)
{
    return QDir(download->downloadDirectory()).filePath(download->downloadFileName());
}

void chooseTarget(QWebEngineDownloadRequest *download)
{
    if (download->isSavePageDownload())
        return;
    download->setDownloadDirectory(Settings::instance()->downloadDirectory());
    if (download->downloadFileName().isEmpty())
        download->setDownloadFileName(download->suggestedFileName());
}

bool showInFileManager(const QString &path)
{
    QDBusInterface fileManager(kFileManagerService, kFileManagerPath, kFileManagerService,
                               QDBusConnection::sessionBus());
    if (!fileManager.isValid())
        return false;
    const QStringList items{ QUrl::fromLocalFile(path).toString() };
    const QDBusMessage reply = fileManager.call(QStringLiteral("ShowItems"), items, QString());
    return reply.type() != QDBusMessage::ErrorMessage;
}

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
    connect(QCoreApplication::instance(), &QCoreApplication::aboutToQuit,
            m_model, &DownloadModel::removePrivateDownloads);
    connect(m_model, &DownloadModel::activeChanged, this, &DownloadManager::activeChanged);
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
    chooseTarget(download);
    m_model->addDownload(download, isPrivate);
    connectNotifications(download);
    acceptOrAsk(download);
    emit downloadStarted();
}

void DownloadManager::acceptOrAsk(QWebEngineDownloadRequest *download)
{
    const bool asksWhereToSave = !download->isSavePageDownload()
        && Settings::instance()->askWhereToSave();
    if (asksWhereToSave)
        requestSaveLocation(download);
    else
        download->accept();
}

void DownloadManager::requestSaveLocation(QWebEngineDownloadRequest *download)
{
    auto *quickRequest = qobject_cast<QQuickWebEngineDownloadRequest *>(download);
    if (!quickRequest) {
        download->accept();
        return;
    }
    emit saveLocationRequested(quickRequest, QUrl::fromLocalFile(targetPathOf(download)));
}

void DownloadManager::connectNotifications(QWebEngineDownloadRequest *download)
{
    connect(download, &QWebEngineDownloadRequest::stateChanged, this,
            [this, download](QWebEngineDownloadRequest::DownloadState state) {
                if (state == QWebEngineDownloadRequest::DownloadCompleted)
                    notifyCompleted(download);
                else if (state == QWebEngineDownloadRequest::DownloadInterrupted)
                    notifyFailed(download);
            });
}

void DownloadManager::notifyCompleted(const QWebEngineDownloadRequest *download)
{
    Notifier::instance()->notify(tr("Download completed"), download->downloadFileName(),
                                 QStringLiteral("download"));
}

void DownloadManager::notifyFailed(const QWebEngineDownloadRequest *download)
{
    const QString reason = download->interruptReasonString();
    Notifier::instance()->notify(tr("Download failed"),
                                 reason.isEmpty() ? download->downloadFileName() : reason,
                                 QStringLiteral("download"));
}

void DownloadManager::pause(int row)
{
    QWebEngineDownloadRequest *download = m_model->downloadAt(row);
    if (download && download->state() == QWebEngineDownloadRequest::DownloadInProgress
        && !download->isPaused())
        download->pause();
}

void DownloadManager::resume(int row)
{
    QWebEngineDownloadRequest *download = m_model->downloadAt(row);
    if (download && download->state() == QWebEngineDownloadRequest::DownloadInProgress
        && download->isPaused())
        download->resume();
}

void DownloadManager::cancel(int row)
{
    QWebEngineDownloadRequest *download = m_model->downloadAt(row);
    if (isActiveDownload(download))
        download->cancel();
}

void DownloadManager::openFile(int row)
{
    const QWebEngineDownloadRequest *download = m_model->downloadAt(row);
    if (!download || download->state() != QWebEngineDownloadRequest::DownloadCompleted)
        return;
    QDesktopServices::openUrl(QUrl::fromLocalFile(targetPathOf(download)));
}

void DownloadManager::showInFolder(int row)
{
    const QWebEngineDownloadRequest *download = m_model->downloadAt(row);
    if (!download || showInFileManager(targetPathOf(download)))
        return;
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
