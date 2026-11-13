#include "adblock/filterlistdownloader.h"

#include <QDir>
#include <QFileInfo>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QSaveFile>

namespace {
constexpr int kTimeoutMilliseconds = 60000;
constexpr int kMinimumListBytes = 1024;

QNetworkRequest requestFor(const FilterListSource &list)
{
    QNetworkRequest request{QUrl(list.url)};
    request.setAttribute(QNetworkRequest::RedirectPolicyAttribute,
                         QNetworkRequest::NoLessSafeRedirectPolicy);
    request.setTransferTimeout(kTimeoutMilliseconds);
    const QFileInfo cached(filterCachePath(list));
    if (cached.exists())
        request.setHeader(QNetworkRequest::IfModifiedSinceHeader, cached.lastModified().toUTC());
    return request;
}

bool saveList(const QString &path, const QByteArray &body)
{
    QSaveFile file(path);
    if (body.size() <= kMinimumListBytes || !file.open(QIODevice::WriteOnly))
        return false;
    file.write(body);
    return file.commit();
}

bool isReplyUsable(QNetworkReply *reply, int status)
{
    return reply->error() == QNetworkReply::NoError && status == 200;
}
}

FilterListDownloader::FilterListDownloader(QObject *parent)
    : QObject(parent)
{
}

void FilterListDownloader::update()
{
    if (isUpdating())
        return;
    if (!m_network)
        m_network = new QNetworkAccessManager(this);
    QDir().mkpath(filterCacheDirectory());
    m_isAnyListCurrent = false;
    m_pendingDownloads = static_cast<int>(filterListSources().size());
    emit updatingChanged();
    for (const FilterListSource &list : filterListSources())
        download(list);
}

void FilterListDownloader::download(const FilterListSource &list)
{
    QNetworkReply *reply = m_network->get(requestFor(list));
    const QString path = filterCachePath(list);
    connect(reply, &QNetworkReply::finished, this, [this, reply, path]() {
        handleReply(reply, path);
    });
}

void FilterListDownloader::handleReply(QNetworkReply *reply, const QString &path)
{
    reply->deleteLater();
    const int status = reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt();
    const bool isSaved = isReplyUsable(reply, status) && saveList(path, reply->readAll());
    if (isSaved || status == 304)
        m_isAnyListCurrent = true;
    finishOneList();
}

void FilterListDownloader::finishOneList()
{
    if (--m_pendingDownloads > 0)
        return;
    emit finished(m_isAnyListCurrent);
    emit updatingChanged();
}
