#pragma once

#include <QString>
#include <QVariantList>

namespace ExtensionPins {

bool isPinned(const QString &id);
void setPinned(const QString &id, bool isPinned);
QVariantList onlyPinned(const QVariantList &entries);

}
