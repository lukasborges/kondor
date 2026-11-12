#pragma once

#include <QAbstractListModel>
#include <QDateTime>
#include <QList>
#include <QSqlQuery>
#include <optional>
#include <QTimer>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>

class HistoryModel : public QAbstractListModel
{
    Q_OBJECT
    QML_ELEMENT
    QML_UNCREATABLE("Use HistoryManager.model")

    Q_PROPERTY(QString filter READ filter WRITE setFilter NOTIFY filterChanged)
    Q_PROPERTY(int count READ count NOTIFY countChanged)
    Q_PROPERTY(bool active READ active WRITE setActive NOTIFY activeChanged)

public:
    enum Roles {
        IdRole = Qt::UserRole + 1,
        UrlRole,
        TitleRole,
        VisitedAtRole,
        DayLabelRole,
        TimeRole,
    };

    explicit HistoryModel(QObject *parent = nullptr);

    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role) const override;
    QHash<int, QByteArray> roleNames() const override;

    QString filter() const { return m_filter; }
    void setFilter(const QString &filter);
    int count() const { return int(m_entries.size()); }
    bool active() const { return m_active; }
    void setActive(bool active);

        void refresh();
        void scheduleRefresh();

    Q_INVOKABLE QString urlAt(int index) const;

signals:
    void filterChanged();
    void countChanged();
    void activeChanged();

private:
    struct Entry {
        qint64 id = 0;
        QUrl url;
        QString title;
        QDateTime visitedAt;
        QString dayLabel;
    };

    static Entry entryOf(QSqlQuery &row);
    static QVariant roleValue(const Entry &entry, int role);
    std::optional<QSqlQuery> queryEntries() const;
    QList<Entry> loadEntries() const;
    static QString dayLabel(const QDateTime &time);
    static QString timeLabel(const QDateTime &time);

    QString m_filter;
    QList<Entry> m_entries;
    QTimer m_refreshTimer;
    bool m_active = false;
};
