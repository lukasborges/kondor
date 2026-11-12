#include "extensions/extensionsettings.h"

#include <QVariantList>

#include <algorithm>

namespace {

using Sanitizer = QVariant (*)(const QVariantMap &setting, const QVariant &value);

struct TypedSanitizer {
    const char *type;
    Sanitizer sanitize;
};

QVariant fallbackOf(const QVariantMap &setting)
{
    return setting.value(QStringLiteral("default"));
}

double clampedNumber(const QVariantMap &setting, double number)
{
    if (setting.contains(QStringLiteral("min")))
        number = qMax(number, setting.value(QStringLiteral("min")).toDouble());
    if (setting.contains(QStringLiteral("max")))
        number = qMin(number, setting.value(QStringLiteral("max")).toDouble());
    return number;
}

QVariant sanitizeBool(const QVariantMap &setting, const QVariant &value)
{
    return value.metaType().id() == QMetaType::Bool ? value.toBool() : fallbackOf(setting).toBool();
}

QVariant sanitizeNumber(const QVariantMap &setting, const QVariant &value)
{
    bool isNumber = false;
    const double number = value.toDouble(&isNumber);
    return isNumber ? QVariant(clampedNumber(setting, number)) : fallbackOf(setting);
}

bool offersChoice(const QVariantList &choices, const QVariant &value)
{
    return std::any_of(choices.begin(), choices.end(), [&value](const QVariant &choice) {
        return choice.toMap().value(QStringLiteral("value")) == value;
    });
}

QVariant sanitizeChoice(const QVariantMap &setting, const QVariant &value)
{
    const QVariantList choices = setting.value(QStringLiteral("choices")).toList();
    return offersChoice(choices, value) ? value : fallbackOf(setting);
}

QVariant sanitizeString(const QVariantMap &setting, const QVariant &value)
{
    return value.metaType().id() == QMetaType::QString ? value : fallbackOf(setting);
}

const TypedSanitizer kSanitizers[] = {
    {"bool", sanitizeBool},
    {"number", sanitizeNumber},
    {"choice", sanitizeChoice},
};

Sanitizer sanitizerFor(const QString &type)
{
    for (const TypedSanitizer &entry : kSanitizers) {
        if (type == QLatin1String(entry.type))
            return entry.sanitize;
    }
    return sanitizeString;
}

}

QVariant sanitizeSetting(const QVariantMap &setting, const QVariant &value)
{
    const QString type = setting.value(QStringLiteral("type")).toString();
    return sanitizerFor(type)(setting, value);
}
