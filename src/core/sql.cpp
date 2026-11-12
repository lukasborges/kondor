#include "core/sql.h"

#include "core/database.h"

namespace Sql {

namespace {

bool bindAndExecute(QSqlQuery &query, const QVariantList &values)
{
    for (const QVariant &value : values)
        query.addBindValue(value);
    return query.exec();
}

QSqlDatabase openedHandle()
{
    return Database::instance()->handle();
}

}

std::optional<QSqlQuery> run(const QString &statement, const QVariantList &values)
{
    if (!Database::instance()->isValid())
        return std::nullopt;
    QSqlQuery query(openedHandle());
    if (!query.prepare(statement) || !bindAndExecute(query, values))
        return std::nullopt;
    return query;
}

QList<qint64> ids(const QString &statement, const QVariantList &values)
{
    QList<qint64> result;
    auto query = run(statement, values);
    while (query && query->next())
        result.append(query->value(0).toLongLong());
    return result;
}

bool inTransaction(const std::function<bool()> &work)
{
    QSqlDatabase database = openedHandle();
    if (!database.transaction())
        return false;
    if (work() && database.commit())
        return true;
    database.rollback();
    return false;
}

QVariant idOrNull(qint64 id)
{
    return id > 0 ? QVariant(id) : QVariant(QMetaType::fromType<qint64>());
}

}
