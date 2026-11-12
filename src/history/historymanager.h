#pragma once

#include <QObject>
#include <QUrl>
#include <QVariantList>
#include <optional>
#include <QtQmlIntegration/qqmlintegration.h>

#include "history/historymodel.h"

class QQmlEngine;
class QJSEngine;

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
    Q_INVOKABLE QVariantList topSites(int limit) const;
    Q_INVOKABLE QVariantList suggest(const QString &text, int limit = 6) const;
    Q_INVOKABLE QVariantList recentToday(int limit) const;
    Q_INVOKABLE QString hostCompletion(const QString &text) const;

    HistoryModel *model() const;

private:
    explicit HistoryManager(QObject *parent = nullptr);

    static bool isTracked(const QUrl &url);
    static std::optional<qint64> recentVisitIdOf(const QString &url, qint64 now);
    static bool mergeIntoRecentVisit(const QString &url, const QString &title, qint64 now);
    static bool insertVisit(const QString &url, const QString &title, qint64 now);
    static void updateTitleOf(qint64 id, const QString &title);

    HistoryModel *m_model = nullptr;
};
