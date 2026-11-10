#pragma once

#include <QObject>
#include <QSettings>
#include <QStringList>
#include <QVariant>
#include <QtQmlIntegration/qqmlintegration.h>

class QQmlEngine;
class QJSEngine;

// QML singleton `Settings`: user preferences persisted in
// ~/.config/KDE/Kondor.conf through QSettings. Every setter writes and syncs
// immediately, so changes apply without a restart.
class Settings : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    Q_PROPERTY(QString homePage READ homePage WRITE setHomePage NOTIFY homePageChanged)
    Q_PROPERTY(QString searchEngine READ searchEngine WRITE setSearchEngine
                   NOTIFY searchEngineChanged)
    Q_PROPERTY(QString customSearchUrl READ customSearchUrl WRITE setCustomSearchUrl
                   NOTIFY customSearchUrlChanged)
    Q_PROPERTY(QString downloadDirectory READ downloadDirectory WRITE setDownloadDirectory
                   NOTIFY downloadDirectoryChanged)
    Q_PROPERTY(bool downloadDirectoryValid READ downloadDirectoryValid
                   NOTIFY downloadDirectoryChanged)
    Q_PROPERTY(bool askWhereToSave READ askWhereToSave WRITE setAskWhereToSave
                   NOTIFY askWhereToSaveChanged)
    Q_PROPERTY(QString startupBehavior READ startupBehavior WRITE setStartupBehavior
                   NOTIFY startupBehaviorChanged)
    Q_PROPERTY(bool showBookmarksBar READ showBookmarksBar WRITE setShowBookmarksBar
                   NOTIFY showBookmarksBarChanged)
    Q_PROPERTY(bool showTopSites READ showTopSites WRITE setShowTopSites
                   NOTIFY showTopSitesChanged)
    Q_PROPERTY(QStringList hiddenTopSites READ hiddenTopSites WRITE setHiddenTopSites
                   NOTIFY hiddenTopSitesChanged)
    Q_PROPERTY(bool clearDataOnExit READ clearDataOnExit WRITE setClearDataOnExit
                   NOTIFY clearDataOnExitChanged)
    Q_PROPERTY(bool blockThirdPartyCookies READ blockThirdPartyCookies
                   WRITE setBlockThirdPartyCookies NOTIFY blockThirdPartyCookiesChanged)
    Q_PROPERTY(bool searchSuggestions READ searchSuggestions WRITE setSearchSuggestions
                   NOTIFY searchSuggestionsChanged)
    Q_PROPERTY(bool spellCheckEnabled READ spellCheckEnabled WRITE setSpellCheckEnabled
                   NOTIFY spellCheckEnabledChanged)
    Q_PROPERTY(QStringList spellCheckLanguages READ spellCheckLanguages
                   WRITE setSpellCheckLanguages NOTIFY spellCheckLanguagesChanged)

public:
    static Settings *instance();
    static Settings *create(QQmlEngine *engine, QJSEngine *jsEngine);

    QString homePage() const { return m_homePage; }
    QString searchEngine() const { return m_searchEngine; }
    QString customSearchUrl() const { return m_customSearchUrl; }
    // Falls back to QStandardPaths::DownloadLocation when the configured
    // folder no longer exists.
    QString downloadDirectory() const;
    bool askWhereToSave() const { return m_askWhereToSave; }
    QString startupBehavior() const { return m_startupBehavior; }
    bool showBookmarksBar() const { return m_showBookmarksBar; }
    bool showTopSites() const { return m_showTopSites; }
    QStringList hiddenTopSites() const { return m_hiddenTopSites; }
    bool clearDataOnExit() const { return m_clearDataOnExit; }
    bool blockThirdPartyCookies() const { return m_blockThirdPartyCookies; }
    bool searchSuggestions() const { return m_searchSuggestions; }
    bool spellCheckEnabled() const { return m_spellCheckEnabled; }
    QStringList spellCheckLanguages() const { return m_spellCheckLanguages; }

    void setHomePage(const QString &homePage);
    void setSearchEngine(const QString &searchEngine);
    void setCustomSearchUrl(const QString &customSearchUrl);
    void setDownloadDirectory(const QString &downloadDirectory);
    void setAskWhereToSave(bool askWhereToSave);
    void setStartupBehavior(const QString &startupBehavior);
    void setShowBookmarksBar(bool showBookmarksBar);
    void setShowTopSites(bool showTopSites);
    void setHiddenTopSites(const QStringList &hiddenTopSites);
    void setClearDataOnExit(bool clearDataOnExit);
    void setBlockThirdPartyCookies(bool blockThirdPartyCookies);
    void setSearchSuggestions(bool searchSuggestions);
    void setSpellCheckEnabled(bool spellCheckEnabled);
    void setSpellCheckLanguages(const QStringList &spellCheckLanguages);

    // Default value of the option with this property name ("homePage",
    // "searchEngine", …). The only source of truth for defaults: the
    // constructor and the Configure window's Defaults button both use it.
    Q_INVOKABLE QVariant defaultValue(const QString &name) const;

    // Dictionaries Qt WebEngine can use: one entry per `<code>.bdic` file in the
    // directory named by QTWEBENGINE_DICTIONARIES_PATH, as `{ code, name }`
    // with the language's native display name, sorted by name.
    Q_INVOKABLE QVariantList availableSpellCheckLanguages() const;

    // URL template for the selected engine, with %1 where the query goes.
    Q_INVOKABLE QString searchUrlTemplate() const;
    // Display name of the selected engine: "DuckDuckGo", "Google",
    // "Startpage", "Brave Search", "" for a custom engine or "DuckDuckGo"
    // when the custom URL is invalid and search falls back to it.
    Q_INVOKABLE QString searchEngineName() const;
    // False when the configured download folder is missing, so the UI can warn.
    bool downloadDirectoryValid() const;
    // Re-emits downloadDirectoryChanged so the UI re-reads the folder and its
    // validity; call it when a window is shown, since the folder may have been
    // deleted while the app was running.
    Q_INVOKABLE void refreshDownloadDirectory();

signals:
    void homePageChanged();
    void searchEngineChanged();
    void customSearchUrlChanged();
    void downloadDirectoryChanged();
    void askWhereToSaveChanged();
    void startupBehaviorChanged();
    void showBookmarksBarChanged();
    void showTopSitesChanged();
    void hiddenTopSitesChanged();
    void clearDataOnExitChanged();
    void blockThirdPartyCookiesChanged();
    void searchSuggestionsChanged();
    void spellCheckEnabledChanged();
    void spellCheckLanguagesChanged();

private:
    explicit Settings(QObject *parent = nullptr);

    QSettings m_settings;
    QString m_homePage;
    QString m_searchEngine;
    QString m_customSearchUrl;
    QString m_downloadDirectory;
    bool m_askWhereToSave = false;
    QString m_startupBehavior;
    bool m_showBookmarksBar = false;
    bool m_showTopSites = true;
    QStringList m_hiddenTopSites;
    bool m_clearDataOnExit = false;
    bool m_blockThirdPartyCookies = false;
    bool m_searchSuggestions = false;
    bool m_spellCheckEnabled = true;
    QStringList m_spellCheckLanguages;
};
