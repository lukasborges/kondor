#pragma once

#include <QAbstractListModel>
#include <QFileInfo>
#include <QJsonValue>
#include <QList>
#include <QUrl>
#include <QVariantMap>
#include <QWebEngineScript>
#include <QtQmlIntegration/qqmlintegration.h>

#include <optional>

#include "extensions/contentscriptbuilder.h"
#include "extensions/extensionaccess.h"
#include "extensions/extensioninstaller.h"
#include "extensions/extensionstate.h"
#include "extensions/installedextension.h"
#include "extensions/installresult.h"
#include "extensions/packagefile.h"

class ProfileScripts;
class QQmlEngine;
class QJSEngine;
class QQuickWebEngineProfile;

class ExtensionManager : public QAbstractListModel
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    Q_PROPERTY(int count READ count NOTIFY countChanged)
    Q_PROPERTY(int revision READ revision NOTIFY revisionChanged)
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

    static ExtensionManager *instance();
    static ExtensionManager *create(QQmlEngine *engine, QJSEngine *jsEngine);

    ~ExtensionManager() override;

    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role) const override;
    QHash<int, QByteArray> roleNames() const override;

    int count() const { return int(m_entries.size()); }
    int revision() const { return m_revision; }
    QVariantMap pendingInstall() const { return m_pendingPreview; }

    static QString extensionsDirectory();
    void setLocale(const QString &locale) { m_locale = locale; }
    void reload();

    Q_INVOKABLE void inspectFile(const QString &path);
    bool prepareInstall(const PackageFile &file);
    Q_INVOKABLE void confirmInstall();
    Q_INVOKABLE void cancelInstall();
    void openPackageFile(const QString &path);
    static bool isPackageFile(const QString &path);
    InstallResult installPackage(const PackageFile &file, const QString &expectedId);
    InstallResult updatePackage(const PackageFile &file, const QString &expectedId);

    Q_INVOKABLE bool isInstalled(const QString &id) const;
    Q_INVOKABLE QString installedVersion(const QString &id) const;
    QString source(const QString &id) const;
    ExtensionAccess installedAccess(const QString &id) const;
    Q_INVOKABLE void setEnabled(const QString &id, bool enabled);
    Q_INVOKABLE void remove(const QString &id);
    Q_INVOKABLE void setUpdateInfo(const QString &id, bool available, bool needsReview);

    Q_INVOKABLE QVariantMap configurationFor(const QString &id) const;
    Q_INVOKABLE void applyConfiguration(const QString &id, const QVariantMap &configuration);
    Q_INVOKABLE QVariantMap settingValues(const QString &id) const;

    Q_INVOKABLE QVariantList actionExtensions(bool isPrivate) const;
    Q_INVOKABLE bool hasActionExtensions(bool isPrivate) const;
    Q_INVOKABLE bool siteEnabled(const QString &id, const QUrl &url) const;
    Q_INVOKABLE void setSiteEnabled(const QString &id, const QUrl &url, bool enabled);
    Q_INVOKABLE static QString originOf(const QUrl &url);

    void registerProfile(QQuickWebEngineProfile *profile);
    QList<QWebEngineScript> scriptsFor(bool privateProfile) const;
    QString scriptSource(const QString &id, int index, bool privateProfile) const;
    void rebuildScripts();

    bool checkToken(const QString &id, const QString &token) const;
    bool isActive(const QString &id, bool privateTab) const;
    bool hasPermission(const QString &id, const QString &permission) const;
    QString displayName(const QString &id) const;

signals:
    void countChanged();
    void revisionChanged();
    void pendingInstallChanged();
    void settingsChanged(const QString &id);
    void manageRequested();
    void extensionRemoved(const QString &id);

private:
    explicit ExtensionManager(QObject *parent = nullptr);

    struct ConfigurationChange {
        bool settings = false;
        bool privacy = false;
        bool sites = false;
        bool any() const { return settings || privacy || sites; }
    };

    int indexOf(const QString &id) const;
    const InstalledExtension *find(const QString &id) const;
    InstalledExtension *find(const QString &id);
    InstalledExtension makeEntry(const ExtensionPackage &package) const;
    void changed();
    ExtensionInstaller installer() const;
    ContentScriptContext contentScriptContext(const InstalledExtension &entry, int index,
                                              bool privateProfile) const;

    QList<InstalledExtension> scanInstalled() const;
    std::optional<InstalledExtension> loadInstalled(const QFileInfo &info) const;
    void removeRow(int row);
    void deleteStoredData(const QString &id);
    void putEntry(const InstalledExtension &entry);
    void appendRow(const InstalledExtension &entry);
    void replaceRow(int row, const InstalledExtension &entry);

    void discardStaged();
    QVariantMap previewOf(const StagedPackage &staged) const;
    void setPending(const QVariantMap &preview);
    void refusePackage(const PackageFile &file, const QString &error);
    bool installStaged(const StagedPackage &staged, QString &error);
    bool addInstalled(const StagedPackage &staged, QString &error);
    InstallResult finishInstall(const StagedPackage &staged, const InstallResult &refusal);
    InstallResult refusalForWrongId(const StagedPackage &staged, const QString &expectedId) const;
    InstallResult refusalForBroaderAccess(const StagedPackage &staged, const QString &id) const;

    ConfigurationChange storeConfiguration(int row, const QVariantMap &configuration);
    bool storeSettings(const QString &id, const QVariantMap &values);
    bool storeSetting(const QString &id, const QVariantMap &setting, const QVariantMap &values);
    bool storePrivateAllowed(int row, bool isAllowed);
    bool storeDisabledSites(const QString &id, const QStringList &sites);
    void applyStoredSetting(const QString &id, const QVariantMap &setting, QVariantMap &values) const;
    QVariantList settingsWithValues(const InstalledExtension &entry) const;

    QList<InstalledExtension> m_entries;
    ExtensionState m_state;
    ProfileScripts *m_scripts;
    QString m_locale;
    int m_revision = 0;
    QVariantMap m_pendingPreview;
    std::optional<StagedPackage> m_staged;
};
