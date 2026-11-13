#include "extensions/manifest/manifestsections.h"

#include <QJsonArray>
#include <QJsonObject>
#include <QSet>
#include <QStringList>

namespace {

const QStringList &knownSettingTypes()
{
    static const QStringList types{QStringLiteral("bool"),   QStringLiteral("number"),
                                   QStringLiteral("string"), QStringLiteral("text"),
                                   QStringLiteral("choice"), QStringLiteral("color"),
                                   QStringLiteral("keys")};
    return types;
}

QString keyError(const QJsonObject &setting, const QString &where, QSet<QString> &keys)
{
    const QString key = setting.value(QLatin1String("key")).toString();
    if (key.isEmpty() || keys.contains(key))
        return manifestError(QStringLiteral("%1.key: required and unique").arg(where));
    keys.insert(key);
    return QString();
}

QString typeError(const QJsonObject &setting, const QString &where)
{
    if (knownSettingTypes().contains(setting.value(QLatin1String("type")).toString()))
        return QString();
    return manifestError(QStringLiteral("%1.type: unknown setting type").arg(where));
}

QString labelError(const QJsonObject &setting, const QString &where)
{
    if (!setting.value(QLatin1String("label")).toString().isEmpty())
        return QString();
    return manifestError(QStringLiteral("%1.label: required").arg(where));
}

bool isChoiceWithoutChoices(const QJsonObject &setting)
{
    return setting.value(QLatin1String("type")).toString() == QLatin1String("choice")
        && setting.value(QLatin1String("choices")).toArray().isEmpty();
}

QString choicesError(const QJsonObject &setting, const QString &where)
{
    if (!isChoiceWithoutChoices(setting))
        return QString();
    return manifestError(QStringLiteral("%1.choices: required for a choice").arg(where));
}

QString settingError(const QJsonObject &setting, int index, QSet<QString> &keys)
{
    const QString where = QStringLiteral("settings[%1]").arg(index);
    QString error = keyError(setting, where, keys);
    if (error.isEmpty())
        error = typeError(setting, where);
    if (error.isEmpty())
        error = labelError(setting, where);
    if (error.isEmpty())
        error = choicesError(setting, where);
    return error;
}

QSet<QString> keysSettingNames(const QJsonValue &settings)
{
    QSet<QString> names;
    for (const QJsonValue &setting : settings.toArray()) {
        const QJsonObject object = setting.toObject();
        if (object.value(QLatin1String("type")).toString() == QLatin1String("keys"))
            names.insert(object.value(QLatin1String("key")).toString());
    }
    return names;
}

QString keysSettingError(const QJsonObject &item, int index, const QSet<QString> &keysNames)
{
    const QJsonValue reference = item.value(QLatin1String("keysSetting"));
    if (reference.isUndefined() || (reference.isString() && keysNames.contains(reference.toString())))
        return QString();
    return manifestError(
        QStringLiteral("action.items[%1].keysSetting: must name a keys setting").arg(index));
}

QString actionItemError(const QJsonObject &item, int index, QSet<QString> &ids)
{
    const QString id = item.value(QLatin1String("id")).toString();
    const bool isInvalid = id.isEmpty() || ids.contains(id)
        || item.value(QLatin1String("title")).toString().isEmpty();
    ids.insert(id);
    if (!isInvalid)
        return QString();
    return manifestError(
        QStringLiteral("action.items[%1]: needs a unique id and a title").arg(index));
}

QString itemsError(const QJsonArray &items, const QSet<QString> &keysNames)
{
    QSet<QString> ids;
    for (int i = 0; i < items.size(); ++i) {
        const QJsonObject item = items.at(i).toObject();
        QString error = actionItemError(item, i, ids);
        if (error.isEmpty())
            error = keysSettingError(item, i, keysNames);
        if (!error.isEmpty())
            return error;
    }
    return QString();
}

}

QString manifestError(const QString &message)
{
    return QStringLiteral("manifest.json: ") + message;
}

QString settingsError(const QJsonValue &settings)
{
    if (!settings.isUndefined() && !settings.isArray())
        return manifestError(QStringLiteral("settings: must be a list"));
    const QJsonArray array = settings.toArray();
    QSet<QString> keys;
    for (int i = 0; i < array.size(); ++i) {
        const QString error = settingError(array.at(i).toObject(), i, keys);
        if (!error.isEmpty())
            return error;
    }
    return QString();
}

QString actionError(const QJsonValue &action, const QJsonValue &settings)
{
    if (!action.isUndefined() && !action.isObject())
        return manifestError(QStringLiteral("action: must be an object"));
    const QJsonArray items = action.toObject().value(QLatin1String("items")).toArray();
    return itemsError(items, keysSettingNames(settings));
}
