#include "bookmarkmodel.h"

#include "database.h"

#include <QSqlQuery>
#include <QVariant>

namespace {
QString likePattern(const QString &term)
{
    QString pattern;
    pattern.reserve(term.size() + 2);
    for (QChar c : term) {
        if (c == QLatin1Char('\\') || c == QLatin1Char('%') || c == QLatin1Char('_'))
            pattern.append(QLatin1Char('\\'));
        pattern.append(c);
    }
    pattern.prepend(QLatin1Char('%'));
    pattern.append(QLatin1Char('%'));
    return pattern;
}
}

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
    if (!index.isValid() || index.row() < 0 || index.row() >= m_entries.size())
        return {};

    const Entry &entry = m_entries.at(index.row());
    switch (role) {
    case IdRole:
        return entry.id;
    case ParentIdRole:
        return entry.parentId;
    case TitleRole:
        return entry.title;
    case UrlRole:
        return entry.url.toString();
    case IsFolderRole:
        return entry.isFolder;
    default:
        return {};
    }
}

QHash<int, QByteArray> BookmarkModel::roleNames() const
{
    return {
        {IdRole, "id"},
        {ParentIdRole, "parentId"},
        {TitleRole, "title"},
        {UrlRole, "url"},
        {IsFolderRole, "isFolder"},
    };
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
    if (row < 0 || row >= m_entries.size())
        return {};
    return m_entries.at(row).url.toString();
}

qint64 BookmarkModel::idAt(int row) const
{
    if (row < 0 || row >= m_entries.size())
        return -1;
    return m_entries.at(row).id;
}

bool BookmarkModel::isFolderAt(int row) const
{
    if (row < 0 || row >= m_entries.size())
        return false;
    return m_entries.at(row).isFolder;
}

void BookmarkModel::refresh()
{
    Database *db = Database::instance();
    QList<Entry> entries;

    if (db->isValid() && m_folderId >= 0) {
        const QString term = m_filter.trimmed();
        QString sql = QStringLiteral(
            "SELECT id, parent_id, title, url, is_folder FROM bookmarks"
            " WHERE parent_id = ?");
        if (!term.isEmpty())
            sql += QStringLiteral(" AND (title LIKE ? ESCAPE '\\' OR url LIKE ? ESCAPE '\\')");
        sql += QStringLiteral(" ORDER BY position, id");

        QSqlQuery query(db->handle());
        query.prepare(sql);
        query.addBindValue(m_folderId);
        if (!term.isEmpty()) {
            const QString pattern = likePattern(term);
            query.addBindValue(pattern);
            query.addBindValue(pattern);
        }
        if (query.exec()) {
            while (query.next()) {
                Entry entry;
                entry.id = query.value(0).toLongLong();
                entry.parentId = query.value(1).toLongLong();
                entry.title = query.value(2).toString();
                entry.url = QUrl(query.value(3).toString());
                entry.isFolder = query.value(4).toBool();
                entries.append(entry);
            }
        }
    }

    beginResetModel();
    m_entries = entries;
    endResetModel();
    emit countChanged();
}
