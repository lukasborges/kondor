#include "core/settings/settings.h"

#include "core/settings/searchengines.h"
#include "core/settings/settingsdefaults.h"
#include "core/settings/spellcheckdictionaries.h"

#include <QFileInfo>
#include <QStandardPaths>

namespace {

constexpr Settings::Option kHomePage{"General/HomePage", "homePage", &Settings::homePageChanged};
constexpr Settings::Option kSearchEngine{"Search/Engine", "searchEngine", &Settings::searchEngineChanged};
constexpr Settings::Option kCustomSearchUrl{"Search/CustomUrl", "customSearchUrl", &Settings::customSearchUrlChanged};
constexpr Settings::Option kDownloadDirectory{"Downloads/Directory", "downloadDirectory", &Settings::downloadDirectoryChanged};
constexpr Settings::Option kAskWhereToSave{"Downloads/AskWhereToSave", "askWhereToSave", &Settings::askWhereToSaveChanged};
constexpr Settings::Option kStartupBehavior{"General/Startup", "startupBehavior", &Settings::startupBehaviorChanged};
constexpr Settings::Option kShowBookmarksBar{"UI/ShowBookmarksBar", "showBookmarksBar", &Settings::showBookmarksBarChanged};
constexpr Settings::Option kShowTopSites{"NewTab/ShowTopSites", "showTopSites", &Settings::showTopSitesChanged};
constexpr Settings::Option kHiddenTopSites{"NewTab/HiddenTopSites", "hiddenTopSites", &Settings::hiddenTopSitesChanged};
constexpr Settings::Option kClearDataOnExit{"Privacy/ClearOnExit", "clearDataOnExit", &Settings::clearDataOnExitChanged};
constexpr Settings::Option kBlockThirdPartyCookies{"Privacy/BlockThirdPartyCookies", "blockThirdPartyCookies", &Settings::blockThirdPartyCookiesChanged};
constexpr Settings::Option kSearchSuggestions{"Search/Suggestions", "searchSuggestions", &Settings::searchSuggestionsChanged};
constexpr Settings::Option kSpellCheckEnabled{"SpellCheck/Enabled", "spellCheckEnabled", &Settings::spellCheckEnabledChanged};
constexpr Settings::Option kSpellCheckLanguages{"SpellCheck/Languages", "spellCheckLanguages", &Settings::spellCheckLanguagesChanged};
constexpr Settings::Option kReaderFontSize{"Reader/FontSize", "readerFontSize", &Settings::readerFontSizeChanged};
constexpr Settings::Option kReaderSerif{"Reader/Serif", "readerSerif", &Settings::readerSerifChanged};
constexpr Settings::Option kAdBlockEnabled{"AdBlock/Enabled", "adBlockEnabled", &Settings::adBlockEnabledChanged};
constexpr Settings::Option kAdBlockAllowList{"AdBlock/AllowList", "adBlockAllowList", &Settings::adBlockAllowListChanged};
constexpr Settings::Option kAdBlockLastUpdate{"AdBlock/LastUpdate", "adBlockLastUpdate", &Settings::adBlockLastUpdateChanged};
constexpr Settings::Option kOfferToSavePasswords{"Passwords/OfferToSave", "offerToSavePasswords", &Settings::offerToSavePasswordsChanged};
constexpr Settings::Option kPasswordNeverSaveSites{"Passwords/NeverSave", "passwordNeverSaveSites", &Settings::passwordNeverSaveSitesChanged};
constexpr Settings::Option kExtensionsAutoUpdate{"Extensions/AutoUpdate", "extensionsAutoUpdate", &Settings::extensionsAutoUpdateChanged};

int clampedReaderFontSize(int size)
{
    return qBound(12, size, 32);
}

QString downloadLocation()
{
    return QStandardPaths::writableLocation(QStandardPaths::DownloadLocation);
}

}

Settings *Settings::instance()
{
    static Settings *settings = new Settings;
    return settings;
}

Settings *Settings::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(engine)
    Q_UNUSED(jsEngine)
    return instance();
}

template<typename T> T Settings::read(const Option &option) const
{
    const QVariant fallback = defaultValue(QLatin1String(option.name));
    return m_settings.value(QLatin1String(option.key), fallback).template value<T>();
}

template<typename T> void Settings::store(T &member, const T &value, const Option &option)
{
    if (member == value)
        return;
    member = value;
    m_settings.setValue(QLatin1String(option.key), value);
    m_settings.sync();
    emit (this->*option.changed)();
}

Settings::Settings(QObject *parent)
    : QObject(parent)
    , m_settings(QStringLiteral("KDE"), QStringLiteral("Kondor"))
    , m_homePage(read<QString>(kHomePage))
    , m_searchEngine(read<QString>(kSearchEngine))
    , m_customSearchUrl(read<QString>(kCustomSearchUrl))
    , m_downloadDirectory(read<QString>(kDownloadDirectory))
    , m_askWhereToSave(read<bool>(kAskWhereToSave))
    , m_startupBehavior(read<QString>(kStartupBehavior))
    , m_showBookmarksBar(read<bool>(kShowBookmarksBar))
    , m_showTopSites(read<bool>(kShowTopSites))
    , m_hiddenTopSites(read<QStringList>(kHiddenTopSites))
    , m_clearDataOnExit(read<bool>(kClearDataOnExit))
    , m_blockThirdPartyCookies(read<bool>(kBlockThirdPartyCookies))
    , m_searchSuggestions(read<bool>(kSearchSuggestions))
    , m_spellCheckEnabled(read<bool>(kSpellCheckEnabled))
    , m_spellCheckLanguages(read<QStringList>(kSpellCheckLanguages))
    , m_readerFontSize(clampedReaderFontSize(read<int>(kReaderFontSize)))
    , m_readerSerif(read<bool>(kReaderSerif))
    , m_adBlockEnabled(read<bool>(kAdBlockEnabled))
    , m_adBlockAllowList(read<QStringList>(kAdBlockAllowList))
    , m_adBlockLastUpdate(read<QDateTime>(kAdBlockLastUpdate))
    , m_offerToSavePasswords(read<bool>(kOfferToSavePasswords))
    , m_passwordNeverSaveSites(read<QStringList>(kPasswordNeverSaveSites))
    , m_extensionsAutoUpdate(read<bool>(kExtensionsAutoUpdate))
{
}

QVariant Settings::defaultValue(const QString &name) const
{
    return SettingsDefaults::valueFor(name);
}

QString Settings::downloadDirectory() const
{
    return downloadDirectoryValid() ? m_downloadDirectory : downloadLocation();
}

bool Settings::downloadDirectoryValid() const
{
    return QFileInfo(m_downloadDirectory).isDir();
}

void Settings::refreshDownloadDirectory()
{
    emit downloadDirectoryChanged();
}

QVariantList Settings::availableSpellCheckLanguages() const
{
    return SpellCheckDictionaries::availableLanguages();
}

QString Settings::searchUrlTemplate() const
{
    return SearchEngines::urlTemplate(m_searchEngine, m_customSearchUrl);
}

QString Settings::searchEngineName() const
{
    return SearchEngines::displayName(m_searchEngine, m_customSearchUrl);
}

void Settings::setHomePage(const QString &homePage) { store(m_homePage, homePage, kHomePage); }
void Settings::setSearchEngine(const QString &searchEngine) { store(m_searchEngine, searchEngine, kSearchEngine); }
void Settings::setCustomSearchUrl(const QString &customSearchUrl) { store(m_customSearchUrl, customSearchUrl, kCustomSearchUrl); }
void Settings::setDownloadDirectory(const QString &downloadDirectory) { store(m_downloadDirectory, downloadDirectory, kDownloadDirectory); }
void Settings::setAskWhereToSave(bool askWhereToSave) { store(m_askWhereToSave, askWhereToSave, kAskWhereToSave); }
void Settings::setStartupBehavior(const QString &startupBehavior) { store(m_startupBehavior, startupBehavior, kStartupBehavior); }
void Settings::setShowBookmarksBar(bool showBookmarksBar) { store(m_showBookmarksBar, showBookmarksBar, kShowBookmarksBar); }
void Settings::setShowTopSites(bool showTopSites) { store(m_showTopSites, showTopSites, kShowTopSites); }
void Settings::setHiddenTopSites(const QStringList &hiddenTopSites) { store(m_hiddenTopSites, hiddenTopSites, kHiddenTopSites); }
void Settings::setClearDataOnExit(bool clearDataOnExit) { store(m_clearDataOnExit, clearDataOnExit, kClearDataOnExit); }
void Settings::setBlockThirdPartyCookies(bool blockThirdPartyCookies) { store(m_blockThirdPartyCookies, blockThirdPartyCookies, kBlockThirdPartyCookies); }
void Settings::setSearchSuggestions(bool searchSuggestions) { store(m_searchSuggestions, searchSuggestions, kSearchSuggestions); }
void Settings::setSpellCheckEnabled(bool spellCheckEnabled) { store(m_spellCheckEnabled, spellCheckEnabled, kSpellCheckEnabled); }
void Settings::setSpellCheckLanguages(const QStringList &spellCheckLanguages) { store(m_spellCheckLanguages, spellCheckLanguages, kSpellCheckLanguages); }
void Settings::setReaderFontSize(int readerFontSize) { store(m_readerFontSize, clampedReaderFontSize(readerFontSize), kReaderFontSize); }
void Settings::setReaderSerif(bool readerSerif) { store(m_readerSerif, readerSerif, kReaderSerif); }
void Settings::setAdBlockEnabled(bool adBlockEnabled) { store(m_adBlockEnabled, adBlockEnabled, kAdBlockEnabled); }
void Settings::setAdBlockAllowList(const QStringList &adBlockAllowList) { store(m_adBlockAllowList, adBlockAllowList, kAdBlockAllowList); }
void Settings::setAdBlockLastUpdate(const QDateTime &adBlockLastUpdate) { store(m_adBlockLastUpdate, adBlockLastUpdate, kAdBlockLastUpdate); }
void Settings::setOfferToSavePasswords(bool offerToSavePasswords) { store(m_offerToSavePasswords, offerToSavePasswords, kOfferToSavePasswords); }
void Settings::setPasswordNeverSaveSites(const QStringList &passwordNeverSaveSites) { store(m_passwordNeverSaveSites, passwordNeverSaveSites, kPasswordNeverSaveSites); }
void Settings::setExtensionsAutoUpdate(bool extensionsAutoUpdate) { store(m_extensionsAutoUpdate, extensionsAutoUpdate, kExtensionsAutoUpdate); }
