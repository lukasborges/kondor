#pragma once

#include <QString>
#include <QStringList>
#include <QVariantList>

namespace SpellCheckDictionaries {

QString dictionariesPath();
QStringList dictionaryCodes();
QVariantList availableLanguages();

}
