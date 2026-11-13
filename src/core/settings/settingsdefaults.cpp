#include "core/settingsdefaults.h"

#include "core/spellcheckdictionaries.h"

#include <QHash>
#include <QLocale>
#include <QStandardPaths>
#include <QStringList>

namespace SettingsDefaults {

namespace {

using DefaultFactory = QVariant (*)();

QVariant systemSpellCheckLanguages()
{
    const QString system = QLocale::system().name().replace(QLatin1Char('_'), QLatin1Char('-'));
    if (SpellCheckDictionaries::dictionaryCodes().contains(system))
        return QStringList{system};
    return QStringList{QStringLiteral("en-US")};
}

QVariant defaultDownloadDirectory()
{
    return QStandardPaths::writableLocation(QStandardPaths::DownloadLocation);
}

const QHash<QString, DefaultFactory> kFactories = {
    {QStringLiteral("homePage"), [] { return QVariant(QString()); }},
    {QStringLiteral("searchEngine"), [] { return QVariant(QStringLiteral("duckduckgo")); }},
    {QStringLiteral("customSearchUrl"), [] { return QVariant(QString()); }},
    {QStringLiteral("downloadDirectory"), defaultDownloadDirectory},
    {QStringLiteral("askWhereToSave"), [] { return QVariant(false); }},
    {QStringLiteral("startupBehavior"), [] { return QVariant(QStringLiteral("homepage")); }},
    {QStringLiteral("showBookmarksBar"), [] { return QVariant(false); }},
    {QStringLiteral("showTopSites"), [] { return QVariant(true); }},
    {QStringLiteral("hiddenTopSites"), [] { return QVariant(QStringList()); }},
    {QStringLiteral("clearDataOnExit"), [] { return QVariant(false); }},
    {QStringLiteral("blockThirdPartyCookies"), [] { return QVariant(false); }},
    {QStringLiteral("searchSuggestions"), [] { return QVariant(false); }},
    {QStringLiteral("readerFontSize"), [] { return QVariant(18); }},
    {QStringLiteral("readerSerif"), [] { return QVariant(true); }},
    {QStringLiteral("spellCheckEnabled"), [] { return QVariant(true); }},
    {QStringLiteral("spellCheckLanguages"), systemSpellCheckLanguages},
    {QStringLiteral("adBlockEnabled"), [] { return QVariant(true); }},
    {QStringLiteral("adBlockAllowList"), [] { return QVariant(QStringList()); }},
    {QStringLiteral("offerToSavePasswords"), [] { return QVariant(true); }},
    {QStringLiteral("passwordNeverSaveSites"), [] { return QVariant(QStringList()); }},
    {QStringLiteral("extensionsAutoUpdate"), [] { return QVariant(true); }},
};

}

QVariant valueFor(const QString &name)
{
    const DefaultFactory factory = kFactories.value(name, nullptr);
    return factory ? factory() : QVariant();
}

}
