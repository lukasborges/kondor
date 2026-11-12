#include "extensions/localizedmanifest.h"

#include <QJsonArray>
#include <QLocale>

namespace LocalizedManifest {

namespace {

QVariantList localizedChoices(const QJsonArray &choices, const QString &locale)
{
    QVariantList list;
    for (const QJsonValue &choice : choices) {
        const QJsonObject object = choice.toObject();
        list.append(QVariantMap{
            {QStringLiteral("value"), object.value(QLatin1String("value")).toVariant()},
            {QStringLiteral("label"), localized(object, QStringLiteral("label"), locale)},
        });
    }
    return list;
}

QVariantMap localizedSetting(const QJsonObject &setting, const QString &locale)
{
    QVariantMap map = setting.toVariantMap();
    map.insert(QStringLiteral("label"), localized(setting, QStringLiteral("label"), locale));
    const QJsonArray choices = setting.value(QLatin1String("choices")).toArray();
    if (!choices.isEmpty())
        map.insert(QStringLiteral("choices"), localizedChoices(choices, locale));
    return map;
}

QVariantMap localizedActionItem(const QJsonObject &item, const QString &locale)
{
    return QVariantMap{
        {QStringLiteral("id"), item.value(QLatin1String("id")).toString()},
        {QStringLiteral("title"), localized(item, QStringLiteral("title"), locale)},
        {QStringLiteral("checkable"), item.value(QLatin1String("checkable")).toBool()},
        {QStringLiteral("icon"), item.value(QLatin1String("icon")).toString()},
    };
}

}

QString localized(const QJsonObject &object, const QString &key, const QString &locale)
{
    const QString name = locale.isEmpty() ? QLocale::system().name() : locale;
    const QStringList candidates{name, name.section(QLatin1Char('_'), 0, 0)};
    for (const QString &candidate : candidates) {
        const QJsonValue value = object.value(QStringLiteral("%1[%2]").arg(key, candidate));
        if (value.isString() && !value.toString().isEmpty())
            return value.toString();
    }
    return object.value(key).toString();
}

QVariantList settingsSchema(const QJsonObject &manifest, const QString &locale)
{
    QVariantList list;
    const QJsonArray array = manifest.value(QLatin1String("settings")).toArray();
    for (const QJsonValue &value : array)
        list.append(localizedSetting(value.toObject(), locale));
    return list;
}

QVariantMap settingDefaults(const QJsonObject &manifest)
{
    QVariantMap defaults;
    const QJsonArray array = manifest.value(QLatin1String("settings")).toArray();
    for (const QJsonValue &value : array) {
        const QJsonObject setting = value.toObject();
        defaults.insert(setting.value(QLatin1String("key")).toString(),
                        setting.value(QLatin1String("default")).toVariant());
    }
    return defaults;
}

QVariantList actionItems(const QJsonObject &manifest, const QString &locale)
{
    QVariantList items;
    const QJsonArray array = manifest.value(QLatin1String("action")).toObject()
                                 .value(QLatin1String("items")).toArray();
    for (const QJsonValue &value : array)
        items.append(localizedActionItem(value.toObject(), locale));
    return items;
}

}
