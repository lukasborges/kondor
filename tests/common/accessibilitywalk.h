#pragma once

#include <QAccessible>
#include <QQuickItem>
#include <QStringList>

inline bool isUnnamedButton(QQuickItem *item)
{
    if (!item->isVisible() || !item->inherits("QQuickAbstractButton"))
        return false;
    QAccessibleInterface *accessible = QAccessible::queryAccessibleInterface(item);
    return accessible && accessible->text(QAccessible::Name).isEmpty();
}

inline QStringList unnamedButtons(QQuickItem *root)
{
    QStringList found;
    if (isUnnamedButton(root))
        found << QString::fromLatin1(root->metaObject()->className());
    for (QQuickItem *child : root->childItems())
        found << unnamedButtons(child);
    return found;
}
