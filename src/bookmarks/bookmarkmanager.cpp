#include "bookmarks/bookmarkmanager.h"

#include "bookmarks/bookmarkmodel.h"
#include "core/database.h"

#include <QDateTime>
#include <QFile>
#include <QGuiApplication>
#include <QRegularExpression>
#include <QSqlError>
#include <QSqlQuery>
#include <QVariant>

#include <functional>
#include <utility>

namespace {
constexpr auto kImportedFolderTitle = "Imported";

bool isSupportedUrl(const QUrl &url)
{
    if (url.isEmpty())
        return false;
    const QString scheme = url.scheme();
    return scheme == QLatin1String("http") || scheme == QLatin1String("https")
        || scheme == QLatin1String("file");
}

QString parentCondition(qint64 parentId)
{
    return parentId > 0 ? QStringLiteral("parent_id = ?") : QStringLiteral("parent_id IS NULL");
}

// Netscape bookmark files are HTML-ish, not valid XML; a small tolerant
// scanner handles what Firefox and Chrome export.
struct ImportNode {
    bool folder = false;
    QString title;
    QUrl url;
    QList<ImportNode *> children;
};

QString decodeEntities(QString text)
{
    text.replace(QLatin1String("&amp;"), QLatin1String("&"));
    text.replace(QLatin1String("&lt;"), QLatin1String("<"));
    text.replace(QLatin1String("&gt;"), QLatin1String(">"));
    text.replace(QLatin1String("&quot;"), QLatin1String("\""));
    text.replace(QLatin1String("&#39;"), QLatin1String("'"));
    text.replace(QLatin1String("&apos;"), QLatin1String("'"));
    text.replace(QLatin1String("&nbsp;"), QLatin1String(" "));

    static const QRegularExpression numeric(QStringLiteral("&#(x?)([0-9a-fA-F]+);"));
    QString decoded;
    int last = 0;
    auto it = numeric.globalMatch(text);
    while (it.hasNext()) {
        const auto match = it.next();
        decoded += text.mid(last, match.capturedStart() - last);
        bool ok = false;
        const uint codePoint =
            match.captured(2).toUInt(&ok, match.captured(1).isEmpty() ? 10 : 16);
        // Reject invalid code points; QString::fromUcs4() encodes the rest as
        // surrogate pairs, so entities above U+FFFF (e.g. emoji) survive.
        if (!ok || codePoint == 0 || codePoint > 0x10FFFF
            || (codePoint >= 0xD800 && codePoint <= 0xDFFF)) {
            decoded += match.captured(0);
        } else {
            const char32_t value = char32_t(codePoint);
            decoded += QString::fromUcs4(&value, 1);
        }
        last = match.capturedEnd();
    }
    decoded += text.mid(last);
    return decoded;
}

QString cleanTitle(QString text)
{
    text.remove(QRegularExpression(QStringLiteral("<[^>]*>")));
    return decodeEntities(text).simplified();
}

QString attributeValue(const QString &tag, const QString &name)
{
    const QRegularExpression re(
        QStringLiteral("\\b%1\\s*=\\s*(?:\"([^\"]*)\"|'([^']*)')").arg(name),
        QRegularExpression::CaseInsensitiveOption);
    const auto match = re.match(tag);
    if (!match.hasMatch())
        return {};
    return match.captured(1).isEmpty() ? match.captured(2) : match.captured(1);
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

qint64 BookmarkManager::specialFolderId(const QString &special) const
{
    Database *db = Database::instance();
    if (!db->isValid())
        return -1;

    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral("SELECT id FROM bookmarks WHERE special = ? LIMIT 1"));
    query.addBindValue(special);
    if (query.exec() && query.next())
        return query.value(0).toLongLong();
    return -1;
}

qint64 BookmarkManager::toolbarFolderId() const
{
    return specialFolderId(QStringLiteral("toolbar"));
}

qint64 BookmarkManager::otherFolderId() const
{
    return specialFolderId(QStringLiteral("other"));
}

QVariantList BookmarkManager::folders() const
{
    QVariantList rows;
    Database *db = Database::instance();
    if (!db->isValid())
        return rows;

    QList<qint64> roots;
    const qint64 toolbar = toolbarFolderId();
    const qint64 other = otherFolderId();
    if (toolbar > 0)
        roots.append(toolbar);
    if (other > 0)
        roots.append(other);

    // Any other top-level folder (imported trees are normally under "Other
    // Bookmarks", but keep custom roots visible in the manager too).
    QSqlQuery query(db->handle());
    if (query.exec(QStringLiteral(
            "SELECT id FROM bookmarks WHERE parent_id IS NULL AND special IS NULL"
            " ORDER BY position, id"))) {
        while (query.next()) {
            const qint64 id = query.value(0).toLongLong();
            if (!roots.contains(id))
                roots.append(id);
        }
    }

    std::function<void(qint64, int)> walk = [&](qint64 folderId, int depth) {
        QSqlQuery folder(db->handle());
        folder.prepare(QStringLiteral(
            "SELECT id, title, COALESCE(parent_id, 0) FROM bookmarks WHERE id = ? AND is_folder = 1"));
        folder.addBindValue(folderId);
        if (!folder.exec() || !folder.next())
            return;

        QVariantMap row;
        row.insert(QStringLiteral("id"), folderId);
        row.insert(QStringLiteral("title"), folder.value(1).toString());
        row.insert(QStringLiteral("parentId"), folder.value(2).toLongLong());
        row.insert(QStringLiteral("depth"), depth);
        rows.append(row);

        QSqlQuery children(db->handle());
        children.prepare(QStringLiteral(
            "SELECT id FROM bookmarks WHERE parent_id = ? AND is_folder = 1"
            " ORDER BY position, id"));
        children.addBindValue(folderId);
        if (children.exec()) {
            QList<qint64> childIds;
            while (children.next())
                childIds.append(children.value(0).toLongLong());
            for (qint64 childId : childIds)
                walk(childId, depth + 1);
        }
    };

    for (qint64 root : roots)
        walk(root, 0);

    return rows;
}

int BookmarkManager::childCount(qint64 folderId) const
{
    Database *db = Database::instance();
    if (!db->isValid() || folderId <= 0)
        return 0;

    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral("SELECT COUNT(*) FROM bookmarks WHERE parent_id = ?"));
    query.addBindValue(folderId);
    if (query.exec() && query.next())
        return query.value(0).toInt();
    return 0;
}

QVariantList BookmarkManager::folderContents(qint64 folderId) const
{
    QVariantList rows;
    Database *db = Database::instance();
    if (!db->isValid() || folderId <= 0)
        return rows;

    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral(
        "SELECT id, title, url, is_folder FROM bookmarks WHERE parent_id = ?"
        " ORDER BY position, id"));
    query.addBindValue(folderId);
    if (!query.exec())
        return rows;

    while (query.next()) {
        QVariantMap row;
        row.insert(QStringLiteral("id"), query.value(0).toLongLong());
        row.insert(QStringLiteral("title"), query.value(1).toString());
        row.insert(QStringLiteral("url"), query.value(2).toString());
        row.insert(QStringLiteral("isFolder"), query.value(3).toBool());
        rows.append(row);
    }
    return rows;
}

QVariantMap BookmarkManager::bookmark(qint64 id) const
{
    QVariantMap row;
    Database *db = Database::instance();
    if (!db->isValid() || id <= 0)
        return row;

    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral(
        "SELECT id, parent_id, title, url, is_folder, position, special FROM bookmarks"
        " WHERE id = ?"));
    query.addBindValue(id);
    if (query.exec() && query.next()) {
        row.insert(QStringLiteral("id"), query.value(0).toLongLong());
        row.insert(QStringLiteral("parentId"), query.value(1).toLongLong());
        row.insert(QStringLiteral("title"), query.value(2).toString());
        row.insert(QStringLiteral("url"), query.value(3).toString());
        row.insert(QStringLiteral("isFolder"), query.value(4).toBool());
        row.insert(QStringLiteral("position"), query.value(5).toInt());
        row.insert(QStringLiteral("special"), query.value(6).toString());
    }
    return row;
}

bool BookmarkManager::isBookmarked(const QUrl &url) const
{
    return bookmarkIdFor(url) > 0;
}

QVariantList BookmarkManager::search(const QString &text, int limit) const
{
    QVariantList results;
    Database *db = Database::instance();
    const QString needle = text.trimmed();
    if (!db->isValid() || needle.isEmpty() || limit <= 0)
        return results;

    // The needle is data, not a pattern: escape LIKE's wildcards.
    QString pattern = needle;
    pattern.replace(QLatin1String("\\"), QLatin1String("\\\\"));
    pattern.replace(QLatin1String("%"), QLatin1String("\\%"));
    pattern.replace(QLatin1String("_"), QLatin1String("\\_"));
    pattern = QLatin1Char('%') + pattern + QLatin1Char('%');

    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral(
        "SELECT url, title FROM bookmarks"
        " WHERE is_folder = 0 AND (url LIKE ? ESCAPE '\\' OR title LIKE ? ESCAPE '\\')"
        " ORDER BY (title LIKE ? ESCAPE '\\') DESC, title COLLATE NOCASE, id LIMIT ?"));
    query.addBindValue(pattern);
    query.addBindValue(pattern);
    query.addBindValue(pattern);
    query.addBindValue(limit);
    if (!query.exec())
        return results;

    while (query.next()) {
        QVariantMap entry;
        entry.insert(QStringLiteral("type"), QStringLiteral("bookmark"));
        entry.insert(QStringLiteral("url"), query.value(0).toString());
        entry.insert(QStringLiteral("title"), query.value(1).toString());
        results.append(entry);
    }
    return results;
}

qint64 BookmarkManager::bookmarkIdFor(const QUrl &url) const
{
    Database *db = Database::instance();
    if (!db->isValid() || url.isEmpty())
        return -1;

    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral(
        "SELECT id FROM bookmarks WHERE is_folder = 0 AND url = ? ORDER BY id LIMIT 1"));
    query.addBindValue(url.toString());
    if (query.exec() && query.next())
        return query.value(0).toLongLong();
    return -1;
}

bool BookmarkManager::ctrlPressed() const
{
    return QGuiApplication::queryKeyboardModifiers().testFlag(Qt::ControlModifier);
}

qint64 BookmarkManager::insertRow(bool isFolder, const QString &title, const QUrl &url,
                                  qint64 parentId, int position)
{
    Database *db = Database::instance();
    if (!db->isValid())
        return -1;

    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral(
        "INSERT INTO bookmarks (parent_id, is_folder, title, url, position, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?)"));
    if (parentId > 0)
        query.addBindValue(parentId);
    else
        query.addBindValue(QVariant());
    query.addBindValue(isFolder ? 1 : 0);
    query.addBindValue(title);
    query.addBindValue(isFolder || !url.isValid() ? QVariant() : url.toString());
    query.addBindValue(position);
    query.addBindValue(QDateTime::currentMSecsSinceEpoch());
    if (!query.exec()) {
        qWarning("Bookmarks: failed to insert %s: %s", qPrintable(title),
                 qPrintable(query.lastError().text()));
        return -1;
    }
    return query.lastInsertId().toLongLong();
}

int BookmarkManager::firstFreePosition(qint64 parentId) const
{
    Database *db = Database::instance();
    if (!db->isValid())
        return 0;

    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral(
        "SELECT COALESCE(MAX(position), -1) + 1 FROM bookmarks WHERE ")
        + parentCondition(parentId));
    if (parentId > 0)
        query.addBindValue(parentId);
    if (query.exec() && query.next())
        return query.value(0).toInt();
    return 0;
}

qint64 BookmarkManager::addBookmark(const QUrl &url, const QString &title, qint64 folderId)
{
    if (!isSupportedUrl(url))
        return -1;

    // An unknown or non-folder target falls back to "Other Bookmarks", like
    // the browser's default for the star button.
    const QVariantMap target = bookmark(folderId);
    if (folderId <= 0 || target.isEmpty() || !target.value(QStringLiteral("isFolder")).toBool())
        folderId = otherFolderId();
    if (folderId <= 0)
        return -1;

    QString name = title.trimmed();
    if (name.isEmpty())
        name = url.toString();

    const qint64 id = insertRow(false, name, url, folderId, firstFreePosition(folderId));
    if (id > 0)
        notifyChanged();
    return id;
}

qint64 BookmarkManager::addFolder(const QString &title, qint64 parentId)
{
    if (parentId > 0) {
        const QVariantMap parent = bookmark(parentId);
        if (parent.isEmpty() || !parent.value(QStringLiteral("isFolder")).toBool())
            return -1;
    } else {
        parentId = 0;
    }

    QString name = title.trimmed();
    if (name.isEmpty())
        name = tr("New Folder");

    const qint64 id = insertRow(true, name, QUrl(), parentId, firstFreePosition(parentId));
    if (id > 0)
        notifyChanged();
    return id;
}

void BookmarkManager::rename(qint64 id, const QString &title)
{
    const QString name = title.trimmed();
    if (name.isEmpty())
        return;

    Database *db = Database::instance();
    if (!db->isValid())
        return;

    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral("UPDATE bookmarks SET title = ? WHERE id = ?"));
    query.addBindValue(name);
    query.addBindValue(id);
    if (query.exec() && query.numRowsAffected() > 0)
        notifyChanged();
}

void BookmarkManager::setUrl(qint64 id, const QUrl &url)
{
    if (!isSupportedUrl(url))
        return;

    Database *db = Database::instance();
    if (!db->isValid())
        return;

    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral(
        "UPDATE bookmarks SET url = ? WHERE id = ? AND is_folder = 0"));
    query.addBindValue(url.toString());
    query.addBindValue(id);
    if (query.exec() && query.numRowsAffected() > 0)
        notifyChanged();
}

void BookmarkManager::renumber(qint64 parentId, qint64 movedId, int movedPosition)
{
    Database *db = Database::instance();
    if (!db->isValid())
        return;

    QList<qint64> ids;
    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral("SELECT id FROM bookmarks WHERE ") + parentCondition(parentId)
                  + QStringLiteral(" ORDER BY position, id"));
    if (parentId > 0)
        query.addBindValue(parentId);
    if (!query.exec())
        return;
    while (query.next())
        ids.append(query.value(0).toLongLong());

    if (movedId > 0) {
        ids.removeAll(movedId);
        const int position = movedPosition < 0 ? int(ids.size())
                                               : qBound(0, movedPosition, int(ids.size()));
        ids.insert(position, movedId);
    }

    QSqlQuery update(db->handle());
    update.prepare(QStringLiteral("UPDATE bookmarks SET position = ? WHERE id = ?"));
    for (int position = 0; position < ids.size(); ++position) {
        update.addBindValue(position);
        update.addBindValue(ids.at(position));
        update.exec();
    }
}

void BookmarkManager::move(qint64 id, qint64 newParentId, int newPosition)
{
    const QVariantMap item = bookmark(id);
    if (item.isEmpty() || !item.value(QStringLiteral("special")).toString().isEmpty())
        return;

    Database *db = Database::instance();
    if (!db->isValid())
        return;

    if (newParentId > 0) {
        const QVariantMap target = bookmark(newParentId);
        if (target.isEmpty() || !target.value(QStringLiteral("isFolder")).toBool())
            return;
    } else {
        newParentId = 0;
    }

    // Moving a folder into itself (or one of its descendants) would detach
    // that subtree from the tree: refuse it.
    if (item.value(QStringLiteral("isFolder")).toBool()) {
        QSqlQuery descendant(db->handle());
        descendant.prepare(QStringLiteral(
            "WITH RECURSIVE subtree(id) AS ("
            "  SELECT id FROM bookmarks WHERE id = ?"
            "  UNION ALL"
            "  SELECT b.id FROM bookmarks b JOIN subtree s ON b.parent_id = s.id"
            ") SELECT 1 FROM subtree WHERE id = ? LIMIT 1"));
        descendant.addBindValue(id);
        descendant.addBindValue(newParentId);
        if (descendant.exec() && descendant.next())
            return;
    }

    const qint64 oldParentId = item.value(QStringLiteral("parentId")).toLongLong();

    QSqlQuery update(db->handle());
    update.prepare(QStringLiteral("UPDATE bookmarks SET parent_id = ? WHERE id = ?"));
    if (newParentId > 0)
        update.addBindValue(newParentId);
    else
        update.addBindValue(QVariant());
    update.addBindValue(id);
    if (!update.exec())
        return;

    renumber(newParentId, id, newPosition);
    if (oldParentId != newParentId)
        renumber(oldParentId, -1, 0);

    notifyChanged();
}

void BookmarkManager::remove(qint64 id)
{
    const QVariantMap item = bookmark(id);
    if (item.isEmpty() || !item.value(QStringLiteral("special")).toString().isEmpty())
        return;

    Database *db = Database::instance();
    if (!db->isValid())
        return;

    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral(
        "WITH RECURSIVE doomed(id) AS ("
        "  SELECT id FROM bookmarks WHERE id = ?"
        "  UNION ALL"
        "  SELECT b.id FROM bookmarks b JOIN doomed d ON b.parent_id = d.id"
        ") DELETE FROM bookmarks WHERE id IN (SELECT id FROM doomed)"));
    query.addBindValue(id);
    if (!query.exec())
        return;

    renumber(item.value(QStringLiteral("parentId")).toLongLong(), -1, 0);
    notifyChanged();
}

int BookmarkManager::importHtml(const QUrl &fileUrl)
{
    QFile file(fileUrl.toLocalFile());
    if (!file.open(QIODevice::ReadOnly))
        return 0;
    const QString html = QString::fromUtf8(file.readAll());
    file.close();

    ImportNode *root = new ImportNode;
    root->folder = true;
    QList<ImportNode *> owned{root};
    QList<ImportNode *> stack{root};
    ImportNode *pending = nullptr;
    int bookmarks = 0;

    int pos = 0;
    while (pos < html.size()) {
        const int lt = html.indexOf(QLatin1Char('<'), pos);
        if (lt < 0)
            break;
        if (html.mid(lt, 4) == QLatin1String("<!--")) {
            const int end = html.indexOf(QLatin1String("-->"), lt + 4);
            pos = end < 0 ? html.size() : end + 3;
            continue;
        }
        const int gt = html.indexOf(QLatin1Char('>'), lt);
        if (gt < 0)
            break;
        QString raw = html.mid(lt + 1, gt - lt - 1).trimmed();
        pos = gt + 1;

        const bool closing = raw.startsWith(QLatin1Char('/'));
        if (closing)
            raw = raw.mid(1).trimmed();
        int end = 0;
        while (end < raw.size() && !raw.at(end).isSpace() && raw.at(end) != QLatin1Char('/'))
            ++end;
        const QString name = raw.left(end).toLower();
        if (name.isEmpty())
            continue;

        if (name == QLatin1String("h3")) {
            const int close = html.indexOf(QLatin1String("</h3"), pos, Qt::CaseInsensitive);
            if (close < 0)
                break;
            ImportNode *folder = new ImportNode;
            folder->folder = true;
            folder->title = cleanTitle(html.mid(pos, close - pos));
            owned.append(folder);
            stack.last()->children.append(folder);
            pending = folder;
            const int after = html.indexOf(QLatin1Char('>'), close);
            pos = after < 0 ? html.size() : after + 1;
        } else if (name == QLatin1String("dl")) {
            if (closing) {
                if (stack.size() > 1)
                    stack.removeLast();
                pending = nullptr;
            } else if (pending) {
                stack.append(pending);
                pending = nullptr;
            } else {
                // The outer <DL> that wraps the whole file.
                stack.append(stack.last());
            }
        } else if (name == QLatin1String("a") && !closing) {
            const int close = html.indexOf(QLatin1String("</a"), pos, Qt::CaseInsensitive);
            if (close < 0)
                break;
            const QUrl url = QUrl(attributeValue(raw, QStringLiteral("href")).trimmed());
            if (isSupportedUrl(url)) {
                ImportNode *bookmark = new ImportNode;
                bookmark->folder = false;
                bookmark->url = url;
                bookmark->title = cleanTitle(html.mid(pos, close - pos));
                if (bookmark->title.isEmpty())
                    bookmark->title = url.toString();
                owned.append(bookmark);
                stack.last()->children.append(bookmark);
                ++bookmarks;
            }
            const int after = html.indexOf(QLatin1Char('>'), close);
            pos = after < 0 ? html.size() : after + 1;
        }
    }

    if (bookmarks == 0) {
        qDeleteAll(owned);
        return 0;
    }

    Database *db = Database::instance();
    if (!db->isValid()) {
        qDeleteAll(owned);
        return 0;
    }

    if (!db->handle().transaction()) {
        qDeleteAll(owned);
        return 0;
    }

    const qint64 otherId = otherFolderId();
    const qint64 importedFolder =
        insertRow(true, QString::fromLatin1(kImportedFolderTitle), QUrl(), otherId,
                  firstFreePosition(otherId));
    if (importedFolder <= 0) {
        db->handle().rollback();
        qDeleteAll(owned);
        return 0;
    }

    QHash<qint64, int> positions;
    int inserted = 0;
    std::function<void(const ImportNode *, qint64)> insertNode =
        [&](const ImportNode *node, qint64 parentId) {
            int &position = positions[parentId];
            if (node->folder) {
                const qint64 id =
                    insertRow(true, node->title, QUrl(), parentId, position++);
                if (id <= 0)
                    return;
                for (const ImportNode *child : node->children)
                    insertNode(child, id);
            } else {
                if (insertRow(false, node->title, node->url, parentId, position++) > 0)
                    ++inserted;
            }
        };
    for (const ImportNode *child : root->children)
        insertNode(child, importedFolder);

    if (inserted != bookmarks || !db->handle().commit()) {
        db->handle().rollback();
        qDeleteAll(owned);
        return 0;
    }

    qDeleteAll(owned);
    notifyChanged();
    return inserted;
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
