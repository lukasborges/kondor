#pragma once

#include <QAbstractListModel>
#include <QList>
#include <QNetworkAccessManager>
#include <QPointer>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>

#include "extensions/catalog/catalogentry.h"
#include "extensions/state/extensionaccess.h"

class CatalogUpdater;
class QNetworkReply;
class QQmlEngine;
class QJSEngine;

class ExtensionCatalog : public QAbstractListModel
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    Q_PROPERTY(QString state READ state NOTIFY stateChanged)
    Q_PROPERTY(QString errorString READ errorString NOTIFY stateChanged)
    Q_PROPERTY(QString installingId READ installingId NOTIFY installingChanged)
    Q_PROPERTY(QString installError READ installError NOTIFY installErrorChanged)

public:
    enum Roles {
        IdRole = Qt::UserRole + 1,
        NameRole,
        DescriptionRole,
        VersionRole,
        AuthorRole,
        IconSourceRole,
        InstalledRole,
        UpdateAvailableRole,
    };

    static constexpr qint64 kMaxPackageBytes = 5 * 1024 * 1024;

    static ExtensionCatalog *instance();
    static ExtensionCatalog *create(QQmlEngine *engine, QJSEngine *jsEngine);

    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role) const override;
    QHash<int, QByteArray> roleNames() const override;

    QString state() const { return m_state; }
    QString errorString() const { return m_error; }
    QString installingId() const { return m_installingId; }
    QString installError() const { return m_installError; }

    QUrl catalogUrl() const;
    void setCatalogUrl(const QUrl &url) { m_catalogUrl = url; }
    static QString cacheFile();

    Q_INVOKABLE void refresh();
    Q_INVOKABLE void install(const QString &id);
    void startAutoUpdate();
    void checkForUpdates();
    Q_INVOKABLE QUrl contributingUrl() const;
    QNetworkAccessManager &network() { return m_network; }

    bool loadCatalog(const QByteArray &json, QString *error);

    static bool isSilentUpdate(const ExtensionAccess &update, const ExtensionAccess &installed);

signals:
    void stateChanged();
    void installingChanged();
    void installErrorChanged();
    void updatesChecked();

private:
    explicit ExtensionCatalog(QObject *parent = nullptr);
    void setState(const QString &state, const QString &error = QString());
    void setInstalling(const QString &id);
    void setInstallError(const QString &error);
    const CatalogEntry *find(const QString &id) const;
    void emitAllChanged();
    void followInstalledExtensions();
    void showCachedCatalog();
    void handleRefreshed(QNetworkReply *reply);
    void failRefresh(const QString &message);
    void succeedRefresh(const QByteArray &body);
    void downloadForInstall(const CatalogEntry &entry);
    void finishInstallDownload(const QString &name, const QString &path, const QString &error);

    QNetworkAccessManager m_network;
    CatalogUpdater *m_updater;
    QList<CatalogEntry> m_entries;
    QString m_state = QStringLiteral("idle");
    QString m_error;
    QString m_installingId;
    QString m_installError;
    QUrl m_catalogUrl;
    QPointer<QNetworkReply> m_refreshReply;
};
