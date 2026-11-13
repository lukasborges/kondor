#include "bookmarks/bookmarkmanager.h"

#include "bookmarks/storage/bookmarkchecks.h"
#include "bookmarks/storage/bookmarkfoldertree.h"
#include "bookmarks/import/bookmarkhtmlimporter.h"
#include "bookmarks/import/bookmarkhtmlparser.h"
#include "bookmarks/storage/bookmarkqueries.h"
#include "core/database/sql.h"

#include <QFile>
#include <QGuiApplication>

#include <utility>

namespace {

bool updatesRows(const QString &statement, const QVariantList &values)
{
    auto query = Sql::run(statement, values);
    return query && query->numRowsAffected() > 0;
}

QString readUtf8File(const QUrl &fileUrl)
{
    QFile file(fileUrl.toLocalFile());
    if (!file.open(QIODevice::ReadOnly))
        return {};
    return QString::fromUtf8(file.readAll());
}

}

BookmarkManager *BookmarkManager::instance()
{
    static BookmarkManager *manager = new BookmarkManager;
    return manager;
}

BookmarkManager *BookmarkManager::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(engine)
    Q_UNUSED(jsEngine)
    return instance();
}

BookmarkManager::BookmarkManager(QObject *parent)
    : QObject(parent)
    , m_toolbarModel(new BookmarkModel(this))
{
    m_toolbarModel->setFolderId(toolbarFolderId());
}

qint64 BookmarkManager::toolbarFolderId() const
{
    return BookmarkQueries::specialFolderId(QStringLiteral("toolbar"));
}

qint64 BookmarkManager::otherFolderId() const
{
    return BookmarkQueries::specialFolderId(QStringLiteral("other"));
}

QVariantList BookmarkManager::folders() const
{
    return BookmarkFolderTree::folders();
}

int BookmarkManager::childCount(qint64 folderId) const
{
    return BookmarkQueries::childCount(folderId);
}

QVariantList BookmarkManager::folderContents(qint64 folderId) const
{
    return BookmarkQueries::folderContents(folderId);
}

QVariantMap BookmarkManager::bookmark(qint64 id) const
{
    return BookmarkQueries::bookmark(id);
}

bool BookmarkManager::isBookmarked(const QUrl &url) const
{
    return BookmarkQueries::isBookmarked(url);
}

QVariantList BookmarkManager::search(const QString &text, int limit) const
{
    return BookmarkQueries::search(text, limit);
}

qint64 BookmarkManager::bookmarkIdFor(const QUrl &url) const
{
    return BookmarkQueries::bookmarkIdFor(url);
}

bool BookmarkManager::ctrlPressed() const
{
    return QGuiApplication::queryKeyboardModifiers().testFlag(Qt::ControlModifier);
}

qint64 BookmarkManager::insertRowAndNotify(const BookmarkRow &row)
{
    const qint64 id = BookmarkFolderTree::insertRow(row);
    if (id > 0)
        notifyChanged();
    return id;
}

qint64 BookmarkManager::addBookmark(const QUrl &url, const QString &title, qint64 folderId)
{
    if (!isSupportedBookmarkUrl(url))
        return -1;
    const qint64 parentId = BookmarkChecks::folderOrOtherBookmarks(folderId);
    if (parentId <= 0)
        return -1;
    const QString name = title.trimmed();
    return insertRowAndNotify({false, name.isEmpty() ? url.toString() : name, url, parentId,
                               BookmarkFolderTree::firstFreePosition(parentId)});
}

qint64 BookmarkManager::addFolder(const QString &title, qint64 parentId)
{
    if (parentId > 0 && !BookmarkChecks::isFolderId(parentId))
        return -1;
    const qint64 validParentId = qMax<qint64>(parentId, 0);
    const QString name = title.trimmed();
    return insertRowAndNotify({true, name.isEmpty() ? tr("New Folder") : name, QUrl(),
                               validParentId, BookmarkFolderTree::firstFreePosition(validParentId)});
}

void BookmarkManager::rename(qint64 id, const QString &title)
{
    const QString name = title.trimmed();
    if (!name.isEmpty()
        && updatesRows(QStringLiteral("UPDATE bookmarks SET title = ? WHERE id = ?"), {name, id}))
        notifyChanged();
}

void BookmarkManager::setUrl(qint64 id, const QUrl &url)
{
    if (isSupportedBookmarkUrl(url)
        && updatesRows(QStringLiteral("UPDATE bookmarks SET url = ? WHERE id = ? AND is_folder = 0"),
                       {url.toString(), id}))
        notifyChanged();
}

void BookmarkManager::move(qint64 id, qint64 newParentId, int newPosition)
{
    const QVariantMap item = BookmarkQueries::bookmark(id);
    const qint64 parentId = qMax<qint64>(newParentId, 0);
    if (!BookmarkChecks::canMove(item, parentId) || !BookmarkFolderTree::reparent(id, parentId))
        return;
    BookmarkFolderTree::renumber(parentId, id, newPosition);
    const qint64 oldParentId = item.value(QStringLiteral("parentId")).toLongLong();
    if (oldParentId != parentId)
        BookmarkFolderTree::renumber(oldParentId, -1, 0);
    notifyChanged();
}

void BookmarkManager::remove(qint64 id)
{
    const QVariantMap item = BookmarkQueries::bookmark(id);
    if (item.isEmpty() || BookmarkChecks::isSpecialRow(item) || !BookmarkFolderTree::removeSubtree(id))
        return;
    BookmarkFolderTree::renumber(item.value(QStringLiteral("parentId")).toLongLong(), -1, 0);
    notifyChanged();
}

int BookmarkManager::importHtml(const QUrl &fileUrl)
{
    const ParsedBookmarks parsed = BookmarkHtmlParser::parse(readUtf8File(fileUrl));
    const int imported = BookmarkHtmlImporter::import(parsed);
    if (imported > 0)
        notifyChanged();
    return imported;
}

BookmarkModel *BookmarkManager::modelForFolder(qint64 folderId)
{
    if (folderId == toolbarFolderId())
        return m_toolbarModel;
    BookmarkModel *&model = m_folderModels[folderId];
    if (!model) {
        model = new BookmarkModel(this);
        model->setFolderId(folderId);
    }
    return model;
}

void BookmarkManager::notifyChanged()
{
    ++m_revision;
    m_toolbarModel->setFolderId(toolbarFolderId());
    m_toolbarModel->refresh();
    for (BookmarkModel *model : std::as_const(m_folderModels))
        model->refresh();
    emit bookmarksChanged();
}
