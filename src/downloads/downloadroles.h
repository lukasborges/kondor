#pragma once

#include "downloads/downloadmodel.h"

QVariant downloadRoleValue(const DownloadItem &item, int role);
QHash<int, QByteArray> downloadRoleNames();
bool isActiveDownload(const QWebEngineDownloadRequest *download);
bool isFinishedDownload(const QWebEngineDownloadRequest *download);
qreal averageActiveProgress(const QList<QWebEngineDownloadRequest *> &downloads);
QList<QWebEngineDownloadRequest *> liveDownloadsOf(const QList<DownloadItem> &items);
