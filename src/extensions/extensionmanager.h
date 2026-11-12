#pragma once

#include <QAbstractListModel>
#include <QHash>
#include <QJsonValue>
#include <QList>
#include <QPointer>
#include <QSettings>
#include <QUrl>
#include <QVariantMap>
#include <QWebEngineScript>
#include <QtQmlIntegration/qqmlintegration.h>

#include "extensionpackage.h"

class QQmlEngine;
class QJSEngine;
class QQuickWebEngineProfile;

// QML singleton `ExtensionManager` (#107): the installed Kondor extensions.
// It is the list model of Settings → Extensions, installs, updates and removes
// packages, keeps their state, storage and settings, and builds the content
// scripts that ProfileManager's profiles run (docs/extensions/api.md).
class ExtensionManager : public QAbstractListModel
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    Q_PROPERTY(int count READ count NOTIFY countChanged)
    // Bumped on every change that can alter the toolbar menu.
    Q_PROPERTY(int revision READ revision NOTIFY revisionChanged)
    // The install the user is being asked to confirm: empty when none,
    // otherwise see `previewOf()`.
    Q_PROPERTY(QVariantMap pendingInstall READ pendingInstall NOTIFY pendingInstallChanged)

public:
    enum Roles {
        IdRole = Qt::UserRole + 1,
        NameRole,
        DescriptionRole,
        VersionRole,
        AuthorRole,
        HomepageRole,
        IconSourceRole,
        EnabledRole,
        PrivateAllowedRole,
        PermissionsRole,
        HasSettingsRole,
        HasActionRole,
        SourceRole,
        UpdateAvailableRole,
        UpdateNeedsReviewRole,
    };

    static constexpr qint64 kStorageQuota = 1024 * 1024;

    static ExtensionManager *instance();
    static ExtensionManager *create(QQmlEngine *engine, QJSEngine *jsEngine);

    explicit ExtensionManager(QObject *parent = nullptr);
    ~ExtensionManager() override;

    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role) const override;
    QHash<int, QByteArray> roleNames() const override;

    int count() const { return int(m_entries.size()); }
    int revision() const { return m_revision; }
    QVariantMap pendingInstall() const { return m_pendingPreview; }

    // <AppDataLocation>/extensions
    static QString extensionsDirectory();
    // Overrides the locale used for names and labels (tests).
    void setLocale(const QString &locale) { m_locale = locale; }

    // Scans the install directory again.
    void reload();

    // --- Install -----------------------------------------------------------
    // Opens a .kondorext file for the confirmation dialog: fills
    // `pendingInstall` with the preview, or with an error for a bad file.
    Q_INVOKABLE void inspectFile(const QString &path);
    // The same for a package fetched from the catalog (`source` "catalog").
    // `deleteWhenDone` removes the downloaded file afterwards.
    bool prepareInstall(const QString &zipPath, const QString &source, const QString &label,
                        bool deleteWhenDone);
    Q_INVOKABLE void confirmInstall();
    Q_INVOKABLE void cancelInstall();
    // File manager: opens a .kondorext as `inspectFile` and asks the window
    // to show Settings → Extensions.
    void openPackageFile(const QString &path);
    static bool isPackageFile(const QString &path);
    // Installs without asking (silent catalog updates). The new package must
    // have `expectedId`. Returns false and sets `error` on failure.
    bool installPackage(const QString &zipPath, const QString &source,
                        const QString &expectedId, QString *error);

    // --- Installed extensions ----------------------------------------------
    Q_INVOKABLE bool isInstalled(const QString &id) const;
    Q_INVOKABLE QString installedVersion(const QString &id) const;
    QString source(const QString &id) const;
    // Match patterns and permissions of the installed package.
    QStringList installedMatches(const QString &id) const;
    QStringList installedPermissions(const QString &id) const;
    Q_INVOKABLE void setEnabled(const QString &id, bool enabled);
    Q_INVOKABLE void remove(const QString &id);
    Q_INVOKABLE void setUpdateInfo(const QString &id, bool available, bool needsReview);

    // --- Configure dialog --------------------------------------------------
    // `{ name, iconSource, privateAllowed, disabledSites, settings: [ { key,
    // type, label, default, value, ... } ] }`
    Q_INVOKABLE QVariantMap configurationFor(const QString &id) const;
    Q_INVOKABLE void applyConfiguration(const QString &id, const QVariantMap &values,
                                        bool privateAllowed, const QStringList &disabledSites);
    // Settings values (defaults for unset keys).
    Q_INVOKABLE QVariantMap settingValues(const QString &id) const;

    // --- Toolbar menu ------------------------------------------------------
    // Enabled extensions with an action, for a normal or a private tab:
    // `[ { id, name, iconSource, siteToggle, items: [ { id, title, checkable, icon } ] } ]`.
    Q_INVOKABLE QVariantList actionExtensions(bool isPrivate) const;
    Q_INVOKABLE bool hasActionExtensions(bool isPrivate) const;
    Q_INVOKABLE bool siteEnabled(const QString &id, const QUrl &url) const;
    Q_INVOKABLE void setSiteEnabled(const QString &id, const QUrl &url, bool enabled);
    // "https://host" for web pages, empty for anything else.
    Q_INVOKABLE static QString originOf(const QUrl &url);

    // --- Content scripts ---------------------------------------------------
    // Gives the profile the extensions' content scripts, now and after every
    // change. Private profiles only get the extensions allowed there.
    void registerProfile(QQuickWebEngineProfile *profile);
    // The scripts of one kind of profile.
    QList<QWebEngineScript> scriptsFor(bool privateProfile) const;
    // Source of one content script of an extension (metadata block included).
    QString scriptSource(const QString &id, int index, bool privateProfile) const;
    void rebuildScripts();

    // --- Page API support (ExtensionBridge) --------------------------------
    // The extension's token, only for the bridge and the scripts built here.
    bool checkToken(const QString &id, const QString &token) const;
    bool isActive(const QString &id, bool privateTab) const;
    bool hasPermission(const QString &id, const QString &permission) const;
    QString displayName(const QString &id) const;
    QJsonValue storageGet(const QString &id, const QString &key) const;
    bool storageSet(const QString &id, const QString &key, const QJsonValue &value, QString *error);
    void storageRemove(const QString &id, const QString &key);
    QStringList storageKeys(const QString &id) const;

signals:
    void countChanged();
    void revisionChanged();
    void pendingInstallChanged();
    // The settings of one extension changed: open pages should be told.
    void settingsChanged(const QString &id);
    // An external request (file manager) wants Settings → Extensions shown.
    void manageRequested();
    // The extension's package was replaced or removed.
    void extensionRemoved(const QString &id);

private:
    struct Entry {
        ExtensionPackage package;
        bool enabled = true;
        bool privateAllowed = false;
        QString source;
        QString token;
        bool updateAvailable = false;
        bool updateNeedsReview = false;
    };
    struct Staged {
        QString directory;
        ExtensionPackage package;
        QString source;
        QString zipPath;
        bool deleteZip = false;
    };

    int indexOf(const QString &id) const;
    const Entry *find(const QString &id) const;
    Entry *find(const QString &id);
    Entry loadEntry(const ExtensionPackage &package) const;
    QString stateKey(const QString &id, const QString &key) const;
    QStringList disabledSites(const QString &id) const;
    void changed();
    bool stage(const QString &zipPath, const QString &source, Staged *out, QString *error);
    bool commit(Staged *staged, QString *error);
    void discardStaged();
    QVariantMap previewOf(const Staged &staged, const QString &label) const;
    void setPending(const QVariantMap &preview);
    QVariant sanitize(const QVariantMap &setting, const QVariant &value) const;
    QWebEngineScript buildScript(const Entry &entry, int index, bool privateProfile) const;
    void applyScripts(QQuickWebEngineProfile *profile);

    QList<Entry> m_entries;
    mutable QSettings m_state;
    QString m_locale;
    int m_revision = 0;
    QVariantMap m_pendingPreview;
    Staged m_staged;
    bool m_hasStaged = false;
    QString m_pendingLabel;
    QList<QPointer<QQuickWebEngineProfile>> m_profiles;
    QHash<QQuickWebEngineProfile *, QList<QWebEngineScript>> m_inserted;
    bool m_rebuildQueued = false;
};
