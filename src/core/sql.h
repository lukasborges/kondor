#pragma once

#include <QList>
#include <QSqlQuery>
#include <QString>
#include <QVariant>
#include <functional>
#include <optional>

namespace Sql {

std::optional<QSqlQuery> run(const QString &statement, const QVariantList &values = {});
QList<qint64> ids(const QString &statement, const QVariantList &values = {});
bool inTransaction(const std::function<bool()> &work);
QVariant idOrNull(qint64 id);

}
