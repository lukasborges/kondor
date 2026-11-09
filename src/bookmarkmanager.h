#pragma once

#include <QHash>
#include <QList>
#include <QObject>
#include <QString>
#include <QUrl>
#include <QVariantList>
#include <QVariantMap>
#include <QtQmlIntegration/qqmlintegration.h>

#include "bookmarkmodel.h"

class QQmlEngine;
class QJSEngine;

// QML singleton `BookmarkManager`: owns the bookmark tree stored through the
// shared Database block (table `bookmarks`). Every write emits
// `bookmarksChanged`, which refreshes the models and re-evaluates the QML
// bindings that depend on `revision`.
class BookmarkManager : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    Q_PROPERTY(BookmarkModel *toolbarModel READ toolbarModel CONSTANT)
    // All folders as a flat list of {id, title, depth, parentId}, in tree order.
    Q_PROPERTY(QVariantList folders READ folders NOTIFY bookmarksChanged)
    // Bumped after every write, so QML bindings can depend on it.
    Q_PROPERTY(int revision READ revision NOTIFY bookmarksChanged)

public:
    static BookmarkManager *instance();
    static BookmarkManager *create(QQmlEngine *engine, QJSEngine *jsEngine);

    BookmarkModel *toolbarModel() const { return m_toolbarModel; }
    QVariantList folders() const;
    int revision() const { return m_revision; }

    Q_INVOKABLE bool isBookmarked(const QUrl &url) const;
    Q_INVOKABLE qint64 bookmarkIdFor(const QUrl &url) const;
    // Returns the new id, or -1 on failure. An invalid folder falls back to
    // "Other Bookmarks".
    Q_INVOKABLE qint64 addBookmark(const QUrl &url, const QString &title, qint64 folderId);
    // `parentId` <= 0 creates a top-level folder.
    Q_INVOKABLE qint64 addFolder(const QString &title, qint64 parentId);
    Q_INVOKABLE void rename(qint64 id, const QString &title);
    Q_INVOKABLE void setUrl(qint64 id, const QUrl &url);
    // Appends when newPosition < 0.
    Q_INVOKABLE void move(qint64 id, qint64 newParentId, int newPosition);
    // Removes a bookmark, or a folder with everything inside it. The two root
    // folders cannot be removed.
    Q_INVOKABLE void remove(qint64 id);
    // Parses the Netscape bookmark HTML exported by Firefox/Chrome and puts
    // everything under a new "Imported" folder. Returns the number of
    // bookmarks imported.
    Q_INVOKABLE int importHtml(const QUrl &fileUrl);

    Q_INVOKABLE qint64 toolbarFolderId() const;
    Q_INVOKABLE qint64 otherFolderId() const;
    Q_INVOKABLE BookmarkModel *modelForFolder(qint64 folderId);
    // Raw rows of one folder, for menus: {id, title, url, isFolder}.
    Q_INVOKABLE QVariantList folderContents(qint64 folderId) const;
    // {id, parentId, title, url, isFolder, position}; empty when not found.
    Q_INVOKABLE QVariantMap bookmark(qint64 id) const;
    Q_INVOKABLE int childCount(qint64 folderId) const;
    // True while Ctrl is held, so menu actions can honour Ctrl+click.
    Q_INVOKABLE bool ctrlPressed() const;

signals:
    void bookmarksChanged();

private:
    explicit BookmarkManager(QObject *parent = nullptr);

    qint64 specialFolderId(const QString &special) const;
    qint64 insertRow(bool isFolder, const QString &title, const QUrl &url, qint64 parentId,
                     int position);
    int firstFreePosition(qint64 parentId) const;
    void renumber(qint64 parentId, qint64 movedId, int movedPosition);
    void notifyChanged();

    BookmarkModel *m_toolbarModel = nullptr;
    QHash<qint64, BookmarkModel *> m_folderModels;
    int m_revision = 0;
};
