#include "settings.h"

#include <QFileInfo>
#include <QStandardPaths>

namespace {
constexpr auto kHomePage = "General/HomePage";
constexpr auto kSearchEngine = "Search/Engine";
constexpr auto kCustomSearchUrl = "Search/CustomUrl";
constexpr auto kDownloadDirectory = "Downloads/Directory";
constexpr auto kAskWhereToSave = "Downloads/AskWhereToSave";
constexpr auto kStartupBehavior = "General/Startup";
constexpr auto kShowBookmarksBar = "UI/ShowBookmarksBar";
constexpr auto kShowTopSites = "NewTab/ShowTopSites";
constexpr auto kHiddenTopSites = "NewTab/HiddenTopSites";
constexpr auto kClearDataOnExit = "Privacy/ClearOnExit";
constexpr auto kBlockThirdPartyCookies = "Privacy/BlockThirdPartyCookies";
constexpr auto kSearchSuggestions = "Search/Suggestions";

// Option property names, used by defaultValue().
constexpr auto kHomePageName = "homePage";
constexpr auto kSearchEngineName = "searchEngine";
constexpr auto kCustomSearchUrlName = "customSearchUrl";
constexpr auto kDownloadDirectoryName = "downloadDirectory";
constexpr auto kAskWhereToSaveName = "askWhereToSave";
constexpr auto kStartupBehaviorName = "startupBehavior";
constexpr auto kShowBookmarksBarName = "showBookmarksBar";
constexpr auto kShowTopSitesName = "showTopSites";
constexpr auto kHiddenTopSitesName = "hiddenTopSites";
constexpr auto kClearDataOnExitName = "clearDataOnExit";
constexpr auto kBlockThirdPartyCookiesName = "blockThirdPartyCookies";
constexpr auto kSearchSuggestionsName = "searchSuggestions";
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

Settings::Settings(QObject *parent)
    : QObject(parent)
    , m_settings(QStringLiteral("KDE"), QStringLiteral("Kondor"))
    , m_homePage(m_settings.value(QLatin1String(kHomePage),
                                  defaultValue(QLatin1String(kHomePageName))).toString())
    , m_searchEngine(m_settings.value(QLatin1String(kSearchEngine),
                                      defaultValue(QLatin1String(kSearchEngineName))).toString())
    , m_customSearchUrl(m_settings.value(QLatin1String(kCustomSearchUrl),
                                         defaultValue(QLatin1String(kCustomSearchUrlName)))
                            .toString())
    , m_downloadDirectory(m_settings.value(QLatin1String(kDownloadDirectory),
                                           defaultValue(QLatin1String(kDownloadDirectoryName)))
                              .toString())
    , m_askWhereToSave(m_settings.value(QLatin1String(kAskWhereToSave),
                                        defaultValue(QLatin1String(kAskWhereToSaveName))).toBool())
    , m_startupBehavior(m_settings.value(QLatin1String(kStartupBehavior),
                                         defaultValue(QLatin1String(kStartupBehaviorName))).toString())
    , m_showBookmarksBar(m_settings.value(QLatin1String(kShowBookmarksBar),
                                          defaultValue(QLatin1String(kShowBookmarksBarName)))
                             .toBool())
    , m_showTopSites(m_settings.value(QLatin1String(kShowTopSites),
                                      defaultValue(QLatin1String(kShowTopSitesName))).toBool())
    , m_hiddenTopSites(m_settings.value(QLatin1String(kHiddenTopSites),
                                        defaultValue(QLatin1String(kHiddenTopSitesName)))
                           .toStringList())
    , m_clearDataOnExit(m_settings.value(QLatin1String(kClearDataOnExit),
                                         defaultValue(QLatin1String(kClearDataOnExitName))).toBool())
    , m_blockThirdPartyCookies(m_settings.value(QLatin1String(kBlockThirdPartyCookies),
                                                defaultValue(QLatin1String(kBlockThirdPartyCookiesName)))
                                   .toBool())
    , m_searchSuggestions(m_settings.value(QLatin1String(kSearchSuggestions),
                                           defaultValue(QLatin1String(kSearchSuggestionsName)))
                              .toBool())
{
}

QVariant Settings::defaultValue(const QString &name) const
{
    if (name == QLatin1String(kHomePageName))
        return QString();
    if (name == QLatin1String(kSearchEngineName))
        return QStringLiteral("duckduckgo");
    if (name == QLatin1String(kCustomSearchUrlName))
        return QString();
    if (name == QLatin1String(kDownloadDirectoryName))
        return QStandardPaths::writableLocation(QStandardPaths::DownloadLocation);
    if (name == QLatin1String(kAskWhereToSaveName))
        return false;
    if (name == QLatin1String(kStartupBehaviorName))
        return QStringLiteral("homepage");
    if (name == QLatin1String(kShowBookmarksBarName))
        return false;
    if (name == QLatin1String(kShowTopSitesName))
        return true;
    if (name == QLatin1String(kHiddenTopSitesName))
        return QStringList();
    if (name == QLatin1String(kClearDataOnExitName))
        return false;
    if (name == QLatin1String(kBlockThirdPartyCookiesName))
        return false;
    if (name == QLatin1String(kSearchSuggestionsName))
        return false;
    return QVariant();
}

QString Settings::downloadDirectory() const
{
    if (QFileInfo(m_downloadDirectory).isDir())
        return m_downloadDirectory;
    return QStandardPaths::writableLocation(QStandardPaths::DownloadLocation);
}

bool Settings::downloadDirectoryValid() const
{
    return QFileInfo(m_downloadDirectory).isDir();
}

void Settings::refreshDownloadDirectory()
{
    emit downloadDirectoryChanged();
}

QString Settings::searchUrlTemplate() const
{
    if (m_searchEngine == QLatin1String("google"))
        return QStringLiteral("https://www.google.com/search?q=%1");
    if (m_searchEngine == QLatin1String("startpage"))
        return QStringLiteral("https://www.startpage.com/do/search?q=%1");
    if (m_searchEngine == QLatin1String("brave"))
        return QStringLiteral("https://search.brave.com/search?q=%1");
    if (m_searchEngine == QLatin1String("custom")) {
        // Without the placeholder the template is unusable: keep search working
        // with DuckDuckGo while the settings window shows the validation message.
        if (m_customSearchUrl.contains(QLatin1String("%1")))
            return m_customSearchUrl;
    }
    return QStringLiteral("https://duckduckgo.com/?q=%1");
}

QString Settings::searchEngineName() const
{
    if (m_searchEngine == QLatin1String("google"))
        return QStringLiteral("Google");
    if (m_searchEngine == QLatin1String("startpage"))
        return QStringLiteral("Startpage");
    if (m_searchEngine == QLatin1String("brave"))
        return QStringLiteral("Brave Search");
    if (m_searchEngine == QLatin1String("custom")) {
        if (m_customSearchUrl.contains(QLatin1String("%1")))
            return QString();
        // The custom URL is unusable, so search falls back to DuckDuckGo.
        return QStringLiteral("DuckDuckGo");
    }
    return QStringLiteral("DuckDuckGo");
}

void Settings::setHomePage(const QString &homePage)
{
    if (m_homePage == homePage)
        return;
    m_homePage = homePage;
    m_settings.setValue(QLatin1String(kHomePage), m_homePage);
    m_settings.sync();
    emit homePageChanged();
}

void Settings::setSearchEngine(const QString &searchEngine)
{
    if (m_searchEngine == searchEngine)
        return;
    m_searchEngine = searchEngine;
    m_settings.setValue(QLatin1String(kSearchEngine), m_searchEngine);
    m_settings.sync();
    emit searchEngineChanged();
}

void Settings::setCustomSearchUrl(const QString &customSearchUrl)
{
    if (m_customSearchUrl == customSearchUrl)
        return;
    m_customSearchUrl = customSearchUrl;
    m_settings.setValue(QLatin1String(kCustomSearchUrl), m_customSearchUrl);
    m_settings.sync();
    emit customSearchUrlChanged();
}

void Settings::setDownloadDirectory(const QString &downloadDirectory)
{
    if (m_downloadDirectory == downloadDirectory)
        return;
    m_downloadDirectory = downloadDirectory;
    m_settings.setValue(QLatin1String(kDownloadDirectory), m_downloadDirectory);
    m_settings.sync();
    emit downloadDirectoryChanged();
}

void Settings::setAskWhereToSave(bool askWhereToSave)
{
    if (m_askWhereToSave == askWhereToSave)
        return;
    m_askWhereToSave = askWhereToSave;
    m_settings.setValue(QLatin1String(kAskWhereToSave), m_askWhereToSave);
    m_settings.sync();
    emit askWhereToSaveChanged();
}

void Settings::setStartupBehavior(const QString &startupBehavior)
{
    if (m_startupBehavior == startupBehavior)
        return;
    m_startupBehavior = startupBehavior;
    m_settings.setValue(QLatin1String(kStartupBehavior), m_startupBehavior);
    m_settings.sync();
    emit startupBehaviorChanged();
}

void Settings::setShowBookmarksBar(bool showBookmarksBar)
{
    if (m_showBookmarksBar == showBookmarksBar)
        return;
    m_showBookmarksBar = showBookmarksBar;
    m_settings.setValue(QLatin1String(kShowBookmarksBar), m_showBookmarksBar);
    m_settings.sync();
    emit showBookmarksBarChanged();
}

void Settings::setShowTopSites(bool showTopSites)
{
    if (m_showTopSites == showTopSites)
        return;
    m_showTopSites = showTopSites;
    m_settings.setValue(QLatin1String(kShowTopSites), m_showTopSites);
    m_settings.sync();
    emit showTopSitesChanged();
}

void Settings::setHiddenTopSites(const QStringList &hiddenTopSites)
{
    if (m_hiddenTopSites == hiddenTopSites)
        return;
    m_hiddenTopSites = hiddenTopSites;
    m_settings.setValue(QLatin1String(kHiddenTopSites), m_hiddenTopSites);
    m_settings.sync();
    emit hiddenTopSitesChanged();
}

void Settings::setClearDataOnExit(bool clearDataOnExit)
{
    if (m_clearDataOnExit == clearDataOnExit)
        return;
    m_clearDataOnExit = clearDataOnExit;
    m_settings.setValue(QLatin1String(kClearDataOnExit), m_clearDataOnExit);
    m_settings.sync();
    emit clearDataOnExitChanged();
}

void Settings::setBlockThirdPartyCookies(bool blockThirdPartyCookies)
{
    if (m_blockThirdPartyCookies == blockThirdPartyCookies)
        return;
    m_blockThirdPartyCookies = blockThirdPartyCookies;
    m_settings.setValue(QLatin1String(kBlockThirdPartyCookies), m_blockThirdPartyCookies);
    m_settings.sync();
    emit blockThirdPartyCookiesChanged();
}

void Settings::setSearchSuggestions(bool searchSuggestions)
{
    if (m_searchSuggestions == searchSuggestions)
        return;
    m_searchSuggestions = searchSuggestions;
    m_settings.setValue(QLatin1String(kSearchSuggestions), m_searchSuggestions);
    m_settings.sync();
    emit searchSuggestionsChanged();
}
