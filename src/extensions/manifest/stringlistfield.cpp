#include "extensions/manifest/stringlistfield.h"

#include <QJsonArray>

namespace {

QString fieldLabel(const StringListField &field)
{
    return field.path.isEmpty() ? field.key : field.path + QLatin1Char('.') + field.key;
}

std::optional<QStringList> missingList(const StringListField &field, QString &error)
{
    if (!field.isRequired)
        return QStringList();
    error = QStringLiteral("manifest.json: %1: required").arg(fieldLabel(field));
    return std::nullopt;
}

std::optional<QStringList> readStrings(const QJsonArray &array, const StringListField &field,
                                       QString &error)
{
    QStringList list;
    for (int i = 0; i < array.size(); ++i) {
        list.append(array.at(i).toString());
        if (list.last().isEmpty()) {
            error = QStringLiteral("manifest.json: %1[%2]: must be a non-empty string")
                        .arg(fieldLabel(field)).arg(i);
            return std::nullopt;
        }
    }
    return list;
}

}

std::optional<QStringList> readStringList(const QJsonObject &object, const StringListField &field,
                                          QString &error)
{
    const QJsonValue value = object.value(field.key);
    if (value.isUndefined() || value.isNull())
        return missingList(field, error);
    if (value.isArray())
        return readStrings(value.toArray(), field, error);
    error = QStringLiteral("manifest.json: %1: must be a list of strings").arg(fieldLabel(field));
    return std::nullopt;
}
