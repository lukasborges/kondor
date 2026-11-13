#include "extensions/extensionstorage.h"

#include <QCoreApplication>
#include <QJsonArray>
#include <QJsonDocument>

#include "core/database.h"
#include "core/sql.h"

namespace ExtensionStorage {

namespace {

QJsonValue firstElement(const QString &json)
{
    const QJsonDocument document = QJsonDocument::fromJson(json.toUtf8());
    if (document.isArray() && !document.array().isEmpty())
        return document.array().at(0);
    return QJsonValue(QJsonValue::Null);
}

QString encode(const QJsonValue &value)
{
    return QString::fromUtf8(QJsonDocument(QJsonArray{value}).toJson(QJsonDocument::Compact));
}

qint64 bytesUsedByOtherKeys(const QString &id, const QString &key)
{
    auto query = Sql::run(QStringLiteral(
        "SELECT COALESCE(SUM(LENGTH(CAST(key AS BLOB)) + LENGTH(CAST(value AS BLOB))), 0) "
        "FROM extension_storage WHERE extension_id = ? AND key != ?"), {id, key});
    return query && query->next() ? query->value(0).toLongLong() : 0;
}

bool exceedsQuota(const QString &id, const QString &key, const QString &json)
{
    const qint64 total = bytesUsedByOtherKeys(id, key) + key.toUtf8().size() + json.toUtf8().size();
    return total > kStorageQuota;
}

StorageWrite insertValue(const QString &id, const QString &key, const QString &json)
{
    const bool isWritten = Sql::run(QStringLiteral(
        "INSERT OR REPLACE INTO extension_storage (extension_id, key, value) VALUES (?, ?, ?)"),
        {id, key, json}).has_value();
    if (isWritten)
        return {true, QString()};
    return {false, QCoreApplication::translate("ExtensionManager", "Storage is not available")};
}

}

QJsonValue value(const QString &id, const QString &key)
{
    auto query = Sql::run(QStringLiteral(
        "SELECT value FROM extension_storage WHERE extension_id = ? AND key = ?"), {id, key});
    if (!query || !query->next())
        return QJsonValue(QJsonValue::Null);
    return firstElement(query->value(0).toString());
}

StorageWrite setValue(const QString &id, const QString &key, const QJsonValue &value)
{
    if (!Database::instance()->isValid())
        return {false, QCoreApplication::translate("ExtensionManager", "Storage is not available")};
    const QString json = encode(value);
    if (exceedsQuota(id, key, json))
        return {false, QCoreApplication::translate(
                           "ExtensionManager", "The extension's storage is full (limit: 1 MiB)")};
    return insertValue(id, key, json);
}

void removeValue(const QString &id, const QString &key)
{
    Sql::run(QStringLiteral("DELETE FROM extension_storage WHERE extension_id = ? AND key = ?"),
             {id, key});
}

QStringList keys(const QString &id)
{
    QStringList list;
    auto query = Sql::run(QStringLiteral(
        "SELECT key FROM extension_storage WHERE extension_id = ? ORDER BY key"), {id});
    while (query && query->next())
        list.append(query->value(0).toString());
    return list;
}

void removeExtension(const QString &id)
{
    Sql::run(QStringLiteral("DELETE FROM extension_storage WHERE extension_id = ?"), {id});
}

}
