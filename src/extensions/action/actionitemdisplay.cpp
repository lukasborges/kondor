#include "extensions/action/actionitemdisplay.h"

#include <QIcon>
#include <QKeySequence>
#include <QRegularExpression>

namespace {

bool isPlainIconName(const QString &name)
{
    static const QRegularExpression plainName(QStringLiteral("^[A-Za-z0-9_.-]+$"));
    return plainName.match(name).hasMatch();
}

QString themeIconOrEmpty(const QString &name)
{
    return isPlainIconName(name) && QIcon::hasThemeIcon(name) ? name : QString();
}

bool isParsed(const QKeySequence &sequence)
{
    return !sequence.isEmpty() && sequence[0].toCombined() != Qt::Key_unknown;
}

QString nativeShortcut(const QString &portableText)
{
    const QKeySequence sequence = QKeySequence::fromString(portableText, QKeySequence::PortableText);
    return isParsed(sequence) ? sequence.toString(QKeySequence::NativeText) : QString();
}

QString shortcutOf(const QVariantMap &item, const QVariantMap &settingValues)
{
    const QString keysSetting = item.value(QStringLiteral("keysSetting")).toString();
    if (keysSetting.isEmpty())
        return QString();
    return nativeShortcut(settingValues.value(keysSetting).toString());
}

QVariantMap displayed(QVariantMap item, const QVariantMap &settingValues)
{
    item.insert(QStringLiteral("icon"), themeIconOrEmpty(item.value(QStringLiteral("icon")).toString()));
    item.insert(QStringLiteral("shortcut"), shortcutOf(item, settingValues));
    return item;
}

}

QVariantList ActionItemDisplay::forDisplay(const QVariantList &items, const QVariantMap &settingValues)
{
    QVariantList result;
    for (const QVariant &item : items)
        result.append(displayed(item.toMap(), settingValues));
    return result;
}
