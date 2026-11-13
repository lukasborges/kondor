#include "browser/tabs/features/tabextensionitems.h"

TabExtensionItems::TabExtensionItems(QObject *parent)
    : QObject(parent)
{
}

QString TabExtensionItems::keyOf(const QString &extensionId, const QString &itemId)
{
    return extensionId + QLatin1Char('/') + itemId;
}

bool TabExtensionItems::isChecked(const QString &extensionId, const QString &itemId) const
{
    return m_checked.contains(keyOf(extensionId, itemId));
}

void TabExtensionItems::setChecked(const QString &extensionId, const QString &itemId,
                                   bool checked)
{
    if (isChecked(extensionId, itemId) == checked)
        return;
    if (checked)
        m_checked.insert(keyOf(extensionId, itemId));
    else
        m_checked.remove(keyOf(extensionId, itemId));
    emit changed();
}

void TabExtensionItems::trigger(const QString &extensionId, const QString &itemId, bool checkable)
{
    const bool checked = checkable && !isChecked(extensionId, itemId);
    if (checkable)
        setChecked(extensionId, itemId, checked);
    emit triggered(extensionId, itemId, checked);
}
