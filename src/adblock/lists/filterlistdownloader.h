#pragma once

#include "adblock/lists/filterlists.h"

#include <QObject>

class QNetworkAccessManager;
class QNetworkReply;

class FilterListDownloader : public QObject
{
    Q_OBJECT

public:
    explicit FilterListDownloader(QObject *parent = nullptr);

    void update();
    bool isUpdating() const { return m_pendingDownloads > 0; }

signals:
    void updatingChanged();
    void finished(bool isAnyListCurrent);

private:
    void download(const FilterListSource &list);
    void handleReply(QNetworkReply *reply, const QString &path);
    void finishOneList();

    QNetworkAccessManager *m_network = nullptr;
    int m_pendingDownloads = 0;
    bool m_isAnyListCurrent = false;
};
