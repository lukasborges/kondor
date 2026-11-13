#include "core/spellcheckdictionaries.h"

#include <QDir>
#include <QFileInfo>
#include <QLocale>
#include <QVariantMap>

#include <algorithm>

namespace SpellCheckDictionaries {

namespace {

QString capitalized(QString text)
{
    if (!text.isEmpty())
        text[0] = text.at(0).toUpper();
    return text;
}

QString displayName(const QString &code)
{
    const QLocale locale(QString(code).replace(QLatin1Char('-'), QLatin1Char('_')));
    const QString language = capitalized(locale.nativeLanguageName());
    if (language.isEmpty())
        return code;
    const QString territory = locale.nativeTerritoryName();
    return territory.isEmpty() ? language : QStringLiteral("%1 (%2)").arg(language, territory);
}

QVariantMap languageEntry(const QString &code)
{
    return {{QStringLiteral("code"), code}, {QStringLiteral("name"), displayName(code)}};
}

bool isNameLess(const QVariant &a, const QVariant &b)
{
    const QString key = QStringLiteral("name");
    return a.toMap().value(key).toString().localeAwareCompare(b.toMap().value(key).toString()) < 0;
}

}

QString dictionariesPath()
{
    return qEnvironmentVariable("QTWEBENGINE_DICTIONARIES_PATH");
}

QStringList dictionaryCodes()
{
    QStringList codes;
    const QString path = dictionariesPath();
    if (path.isEmpty())
        return codes;
    const QFileInfoList files = QDir(path).entryInfoList({QStringLiteral("*.bdic")}, QDir::Files);
    for (const QFileInfo &file : files)
        codes.append(file.completeBaseName());
    return codes;
}

QVariantList availableLanguages()
{
    QVariantList languages;
    for (const QString &code : dictionaryCodes())
        languages.append(languageEntry(code));
    std::sort(languages.begin(), languages.end(), isNameLess);
    return languages;
}

}
