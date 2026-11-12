#pragma once

#include <QObject>
#include <QUrl>
#include <QVariantList>
#include <QtQmlIntegration/qqmlintegration.h>

#include "historymodel.h"

class QQmlEngine;
class QJSEngine;

// QML singleton `HistoryManager`: writes, queries and clears the browsing
// history of the persistent profile (the privacy barrier lives in QML, which
// never calls this for private tabs).
class HistoryManager : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    Q_PROPERTY(HistoryModel *model READ model CONSTANT)

public:
    static HistoryManager *instance();
    static HistoryManager *create(QQmlEngine *engine, QJSEngine *jsEngine);

    Q_INVOKABLE void addVisit(const QUrl &url, const QString &title);
    Q_INVOKABLE void updateTitle(const QUrl &url, const QString &title);
    Q_INVOKABLE void removeEntry(qint64 id);
    Q_INVOKABLE void clearAll();
    Q_INVOKABLE void clearSince(qint64 msecsSinceEpoch);
    // Up to `limit` hosts visited in the last 90 days, most visited first:
    // each entry is {url, title, host}, one tile per host. Never called for
    // private tabs (the privacy barrier lives in QML).
    Q_INVOKABLE QVariantList topSites(int limit) const;
    // Up to `limit` URLs whose address or title contains `text`, most visited
    // first: each entry is {type: "history", url, title}. Reading is safe from
    // a private tab; the privacy barrier only stops recording.
    Q_INVOKABLE QVariantList suggest(const QString &text, int limit = 6) const;
    // Up to `limit` pages visited since local midnight, most recent first, one
    // row per URL: each entry is {url, title}.
    Q_INVOKABLE QVariantList recentToday(int limit) const;
    // Host of the most visited history URL whose host starts with `text`
    // ("kd" -> "kde.org"), for inline completion in the address bar; empty
    // when there is no match or the text has spaces.
    Q_INVOKABLE QString hostCompletion(const QString &text) const;

    HistoryModel *model() const;

private:
    explicit HistoryManager(QObject *parent = nullptr);

    static bool isTracked(const QUrl &url);

    HistoryModel *m_model = nullptr;
};
