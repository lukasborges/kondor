#pragma once

#include <QAbstractListModel>
#include <QList>
#include <QString>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>

// Items of one bookmark folder, in their stored order. Exposed via
// `BookmarkManager.toolbarModel` and `BookmarkManager.modelForFolder()`;
// refreshes after every bookmark write.
class BookmarkModel : public QAbstractListModel
{
    Q_OBJECT
    QML_ELEMENT
    QML_UNCREATABLE("Use BookmarkManager.toolbarModel or BookmarkManager.modelForFolder()")

    Q_PROPERTY(qint64 folderId READ folderId WRITE setFolderId NOTIFY folderIdChanged)
    Q_PROPERTY(QString filter READ filter WRITE setFilter NOTIFY filterChanged)
    Q_PROPERTY(int count READ count NOTIFY countChanged)

public:
    enum Roles {
        IdRole = Qt::UserRole + 1,
        ParentIdRole,
        TitleRole,
        UrlRole,
        IsFolderRole,
    };

    explicit BookmarkModel(QObject *parent = nullptr);

    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role) const override;
    QHash<int, QByteArray> roleNames() const override;

    qint64 folderId() const { return m_folderId; }
    void setFolderId(qint64 folderId);
    QString filter() const { return m_filter; }
    void setFilter(const QString &filter);
    int count() const { return int(m_entries.size()); }

    Q_INVOKABLE QString urlAt(int row) const;
    Q_INVOKABLE qint64 idAt(int row) const;
    Q_INVOKABLE bool isFolderAt(int row) const;
    // Row of the item with this id in the current (possibly filtered) list,
    // or -1.
    Q_INVOKABLE int rowOf(qint64 id) const;

public slots:
    void refresh();

signals:
    void folderIdChanged();
    void filterChanged();
    void countChanged();

private:
    struct Entry {
        qint64 id = 0;
        qint64 parentId = 0;
        QString title;
        QUrl url;
        bool isFolder = false;
    };

    qint64 m_folderId = -1;
    QString m_filter;
    QList<Entry> m_entries;
};
