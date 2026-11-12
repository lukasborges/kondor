#pragma once

#include <QHash>
#include <QList>
#include <QObject>
#include <QString>
#include <QUrl>
#include <QVariantList>
#include <QVariantMap>
#include <QtQmlIntegration/qqmlintegration.h>

#include "bookmarks/bookmarkmodel.h"
#include "bookmarks/bookmarkrow.h"

class QQmlEngine;
class QJSEngine;

class BookmarkManager : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    Q_PROPERTY(BookmarkModel *toolbarModel READ toolbarModel CONSTANT)
    Q_PROPERTY(QVariantList folders READ folders NOTIFY bookmarksChanged)
    Q_PROPERTY(int revision READ revision NOTIFY bookmarksChanged)

public:
    static BookmarkManager *instance();
    static BookmarkManager *create(QQmlEngine *engine, QJSEngine *jsEngine);

    BookmarkModel *toolbarModel() const { return m_toolbarModel; }
    QVariantList folders() const;
    int revision() const { return m_revision; }

    Q_INVOKABLE bool isBookmarked(const QUrl &url) const;
    Q_INVOKABLE QVariantList search(const QString &text, int limit = 4) const;
    Q_INVOKABLE qint64 bookmarkIdFor(const QUrl &url) const;
    Q_INVOKABLE qint64 addBookmark(const QUrl &url, const QString &title, qint64 folderId);
    Q_INVOKABLE qint64 addFolder(const QString &title, qint64 parentId);
    Q_INVOKABLE void rename(qint64 id, const QString &title);
    Q_INVOKABLE void setUrl(qint64 id, const QUrl &url);
    Q_INVOKABLE void move(qint64 id, qint64 newParentId, int newPosition);
    Q_INVOKABLE void remove(qint64 id);
    Q_INVOKABLE int importHtml(const QUrl &fileUrl);

    Q_INVOKABLE qint64 toolbarFolderId() const;
    Q_INVOKABLE qint64 otherFolderId() const;
    Q_INVOKABLE BookmarkModel *modelForFolder(qint64 folderId);
    Q_INVOKABLE QVariantList folderContents(qint64 folderId) const;
    Q_INVOKABLE QVariantMap bookmark(qint64 id) const;
    Q_INVOKABLE int childCount(qint64 folderId) const;
    Q_INVOKABLE bool ctrlPressed() const;

signals:
    void bookmarksChanged();

private:
    explicit BookmarkManager(QObject *parent = nullptr);

    qint64 insertRowAndNotify(const BookmarkRow &row);
    void notifyChanged();

    BookmarkModel *m_toolbarModel = nullptr;
    QHash<qint64, BookmarkModel *> m_folderModels;
    int m_revision = 0;
};
