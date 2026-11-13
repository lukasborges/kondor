#pragma once

#include <QDateTime>
#include <QObject>
#include <QSettings>
#include <QStringList>
#include <QVariant>
#include <QtQmlIntegration/qqmlintegration.h>

class QQmlEngine;
class QJSEngine;

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
    Q_PROPERTY(int readerFontSize READ readerFontSize WRITE setReaderFontSize
                   NOTIFY readerFontSizeChanged)
    Q_PROPERTY(bool readerSerif READ readerSerif WRITE setReaderSerif NOTIFY readerSerifChanged)
    Q_PROPERTY(bool spellCheckEnabled READ spellCheckEnabled WRITE setSpellCheckEnabled
                   NOTIFY spellCheckEnabledChanged)
    Q_PROPERTY(QStringList spellCheckLanguages READ spellCheckLanguages
                   WRITE setSpellCheckLanguages NOTIFY spellCheckLanguagesChanged)
    Q_PROPERTY(bool adBlockEnabled READ adBlockEnabled WRITE setAdBlockEnabled
                   NOTIFY adBlockEnabledChanged)
    Q_PROPERTY(QStringList adBlockAllowList READ adBlockAllowList WRITE setAdBlockAllowList
                   NOTIFY adBlockAllowListChanged)
    Q_PROPERTY(bool offerToSavePasswords READ offerToSavePasswords WRITE setOfferToSavePasswords
                   NOTIFY offerToSavePasswordsChanged)
    Q_PROPERTY(QStringList passwordNeverSaveSites READ passwordNeverSaveSites
                   WRITE setPasswordNeverSaveSites NOTIFY passwordNeverSaveSitesChanged)
    Q_PROPERTY(bool extensionsAutoUpdate READ extensionsAutoUpdate WRITE setExtensionsAutoUpdate
                   NOTIFY extensionsAutoUpdateChanged)
    Q_PROPERTY(QDateTime adBlockLastUpdate READ adBlockLastUpdate WRITE setAdBlockLastUpdate
                   NOTIFY adBlockLastUpdateChanged)

public:
    struct Option {
        const char *key;
        const char *name;
        void (Settings::*changed)();
    };

    static Settings *instance();
    static Settings *create(QQmlEngine *engine, QJSEngine *jsEngine);

    QString homePage() const { return m_homePage; }
    QString searchEngine() const { return m_searchEngine; }
    QString customSearchUrl() const { return m_customSearchUrl; }
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
    int readerFontSize() const { return m_readerFontSize; }
    bool readerSerif() const { return m_readerSerif; }
    QStringList spellCheckLanguages() const { return m_spellCheckLanguages; }
    bool adBlockEnabled() const { return m_adBlockEnabled; }
    QStringList adBlockAllowList() const { return m_adBlockAllowList; }
    bool offerToSavePasswords() const { return m_offerToSavePasswords; }
    bool extensionsAutoUpdate() const { return m_extensionsAutoUpdate; }
    QStringList passwordNeverSaveSites() const { return m_passwordNeverSaveSites; }
    QDateTime adBlockLastUpdate() const { return m_adBlockLastUpdate; }

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
    void setReaderFontSize(int readerFontSize);
    void setReaderSerif(bool readerSerif);
    void setSpellCheckLanguages(const QStringList &spellCheckLanguages);
    void setAdBlockEnabled(bool adBlockEnabled);
    void setAdBlockAllowList(const QStringList &adBlockAllowList);
    void setAdBlockLastUpdate(const QDateTime &adBlockLastUpdate);
    void setOfferToSavePasswords(bool offerToSavePasswords);
    void setPasswordNeverSaveSites(const QStringList &passwordNeverSaveSites);
    void setExtensionsAutoUpdate(bool extensionsAutoUpdate);

    Q_INVOKABLE QVariant defaultValue(const QString &name) const;

    Q_INVOKABLE QVariantList availableSpellCheckLanguages() const;

    Q_INVOKABLE QString searchUrlTemplate() const;
    Q_INVOKABLE QString searchEngineName() const;
    bool downloadDirectoryValid() const;
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
    void readerFontSizeChanged();
    void readerSerifChanged();
    void spellCheckLanguagesChanged();
    void adBlockEnabledChanged();
    void adBlockAllowListChanged();
    void adBlockLastUpdateChanged();
    void offerToSavePasswordsChanged();
    void passwordNeverSaveSitesChanged();
    void extensionsAutoUpdateChanged();

private:
    explicit Settings(QObject *parent = nullptr);

    template<typename T> T read(const Option &option) const;
    template<typename T> void store(T &member, const T &value, const Option &option);

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
    bool m_adBlockEnabled = true;
    QStringList m_adBlockAllowList;
    QDateTime m_adBlockLastUpdate;
    int m_readerFontSize = 18;
    bool m_readerSerif = true;
    bool m_offerToSavePasswords = true;
    QStringList m_passwordNeverSaveSites;
    bool m_extensionsAutoUpdate = true;
};
