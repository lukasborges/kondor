#include "bookmarks/bookmarkmodel.h"

#include "bookmarks/storage/bookmarkqueries.h"
#include "core/database/sql.h"

#include <QSqlQuery>
#include <QVariant>

#include <utility>

BookmarkModel::BookmarkModel(QObject *parent)
    : QAbstractListModel(parent)
{
}

int BookmarkModel::rowCount(const QModelIndex &parent) const
{
    return parent.isValid() ? 0 : int(m_entries.size());
}

QVariant BookmarkModel::data(const QModelIndex &index, int role) const
{
    if (!index.isValid() || !hasRow(index.row()))
        return {};
    return fieldOf(m_entries.at(index.row()), role);
}

QVariant BookmarkModel::fieldOf(const Entry &entry, int role)
{
    switch (role) {
    case IdRole: return entry.id;
    case ParentIdRole: return entry.parentId;
    case TitleRole: return entry.title;
    case UrlRole: return entry.url.toString();
    case IsFolderRole: return entry.isFolder;
    default: return {};
    }
}

QHash<int, QByteArray> BookmarkModel::roleNames() const
{
    static const QHash<int, QByteArray> roles{
        {IdRole, "id"},
        {ParentIdRole, "parentId"},
        {TitleRole, "title"},
        {UrlRole, "url"},
        {IsFolderRole, "isFolder"},
    };
    return roles;
}

void BookmarkModel::setFolderId(qint64 folderId)
{
    if (m_folderId == folderId)
        return;
    m_folderId = folderId;
    emit folderIdChanged();
    refresh();
}

void BookmarkModel::setFilter(const QString &filter)
{
    if (m_filter == filter)
        return;
    m_filter = filter;
    emit filterChanged();
    refresh();
}

QString BookmarkModel::urlAt(int row) const
{
    return hasRow(row) ? m_entries.at(row).url.toString() : QString();
}

qint64 BookmarkModel::idAt(int row) const
{
    return hasRow(row) ? m_entries.at(row).id : -1;
}

bool BookmarkModel::isFolderAt(int row) const
{
    return hasRow(row) && m_entries.at(row).isFolder;
}

int BookmarkModel::rowOf(qint64 id) const
{
    for (int row = 0; row < m_entries.size(); ++row) {
        if (m_entries.at(row).id == id)
            return row;
    }
    return -1;
}

QString BookmarkModel::selectStatement() const
{
    QString statement = QStringLiteral(
        "SELECT id, parent_id, title, url, is_folder FROM bookmarks WHERE parent_id = ?");
    if (!m_filter.trimmed().isEmpty())
        statement += QStringLiteral(" AND (title LIKE ? ESCAPE '\\' OR url LIKE ? ESCAPE '\\')");
    return statement + QStringLiteral(" ORDER BY position, id");
}

QVariantList BookmarkModel::bindValues() const
{
    const QString term = m_filter.trimmed();
    if (term.isEmpty())
        return {m_folderId};
    const QString pattern = BookmarkQueries::likePattern(term);
    return {m_folderId, pattern, pattern};
}

BookmarkModel::Entry BookmarkModel::readEntry(const QSqlQuery &query)
{
    return {query.value(0).toLongLong(), query.value(1).toLongLong(),
            query.value(2).toString(), QUrl(query.value(3).toString()),
            query.value(4).toBool()};
}

QList<BookmarkModel::Entry> BookmarkModel::loadEntries() const
{
    QList<Entry> entries;
    if (m_folderId < 0)
        return entries;
    auto query = Sql::run(selectStatement(), bindValues());
    while (query && query->next())
        entries.append(readEntry(*query));
    return entries;
}

void BookmarkModel::refresh()
{
    QList<Entry> entries = loadEntries();
    beginResetModel();
    m_entries = std::move(entries);
    endResetModel();
    emit countChanged();
}
