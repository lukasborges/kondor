#include "browser/suggestionlist.h"

#include <QJsonArray>
#include <QJsonDocument>

namespace {
constexpr int kMaxSuggestions = 6;

bool isUsableSuggestion(const QJsonValue &value)
{
    return value.isString() && !value.toString().isEmpty();
}
}

QStringList suggestionsFromJson(const QByteArray &body)
{
    const QJsonArray root = QJsonDocument::fromJson(body).array();
    if (root.size() < 2 || !root.at(1).isArray())
        return {};
    QStringList items;
    for (const QJsonValue &value : root.at(1).toArray()) {
        if (isUsableSuggestion(value))
            items.append(value.toString());
    }
    return items.mid(0, kMaxSuggestions);
}
