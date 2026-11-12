#pragma once

#include <QDateTime>
#include <QList>
#include <QStringList>
#include <QVariant>

struct StorageRow {
    const char *property;
    const char *key;
    QVariant value;
};

inline const QVariant kText(QStringLiteral("changed"));
inline const QVariant kList(QStringList{QStringLiteral("a.example")});

inline const QList<StorageRow> kStorageRows = {
    {"homePage", "General/HomePage", kText},
    {"searchEngine", "Search/Engine", kText},
    {"customSearchUrl", "Search/CustomUrl", kText},
    {"downloadDirectory", "Downloads/Directory", kText},
    {"askWhereToSave", "Downloads/AskWhereToSave", QVariant(true)},
    {"startupBehavior", "General/Startup", kText},
    {"showBookmarksBar", "UI/ShowBookmarksBar", QVariant(true)},
    {"showTopSites", "NewTab/ShowTopSites", QVariant(false)},
    {"hiddenTopSites", "NewTab/HiddenTopSites", kList},
    {"clearDataOnExit", "Privacy/ClearOnExit", QVariant(true)},
    {"blockThirdPartyCookies", "Privacy/BlockThirdPartyCookies", QVariant(true)},
    {"searchSuggestions", "Search/Suggestions", QVariant(true)},
    {"spellCheckEnabled", "SpellCheck/Enabled", QVariant(false)},
    {"spellCheckLanguages", "SpellCheck/Languages", kList},
    {"readerFontSize", "Reader/FontSize", QVariant(24)},
    {"readerSerif", "Reader/Serif", QVariant(false)},
    {"adBlockLastUpdate", "AdBlock/LastUpdate", QVariant(QDateTime::fromSecsSinceEpoch(1000000))},
    {"adBlockEnabled", "AdBlock/Enabled", QVariant(false)},
    {"adBlockAllowList", "AdBlock/AllowList", kList},
    {"offerToSavePasswords", "Passwords/OfferToSave", QVariant(false)},
    {"passwordNeverSaveSites", "Passwords/NeverSave", kList},
    {"extensionsAutoUpdate", "Extensions/AutoUpdate", QVariant(false)},
};
