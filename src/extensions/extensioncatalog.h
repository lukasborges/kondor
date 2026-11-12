#pragma once

#include <QAbstractListModel>
#include <QJsonObject>
#include <QList>
#include <QNetworkAccessManager>
#include <QPointer>
#include <QStringList>
#include <QTimer>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>

class QNetworkReply;
class QQmlEngine;
class QJSEngine;

// QML singleton `ExtensionCatalog` (#107): the community catalog published by
// the lukasborges/kondor-extensions repository (#108). It lists the entries,
// downloads and verifies packages (size and SHA-256), and updates the
// installed catalog extensions in the background.
class ExtensionCatalog : public QAbstractListModel
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    // "idle", "loading", "ready" or "error".
    Q_PROPERTY(QString state READ state NOTIFY stateChanged)
    Q_PROPERTY(QString errorString READ errorString NOTIFY stateChanged)
    // The entry being downloaded for an install, or empty.
    Q_PROPERTY(QString installingId READ installingId NOTIFY installingChanged)
    // Why the last install failed, empty after a successful start.
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

    explicit ExtensionCatalog(QObject *parent = nullptr);

    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role) const override;
    QHash<int, QByteArray> roleNames() const override;

    QString state() const { return m_state; }
    QString errorString() const { return m_error; }
    QString installingId() const { return m_installingId; }
    QString installError() const { return m_installError; }

    // The catalog URL: the KONDOR_EXTENSIONS_CATALOG_URL environment variable
    // (for local test catalogs), else the published one.
    QUrl catalogUrl() const;
    void setCatalogUrl(const QUrl &url) { m_catalogUrl = url; }
    // Where the last good catalog is cached.
    static QString cacheFile();

    // Fetches the catalog again.
    Q_INVOKABLE void refresh();
    // Downloads the package of an entry, checks it and opens the install
    // confirmation (ExtensionManager::pendingInstall).
    Q_INVOKABLE void install(const QString &id);
    // Checks for newer versions now and applies the silent ones. Called at
    // startup and every 24 hours when "Update extensions automatically" is on.
    void startAutoUpdate();
    void checkForUpdates();
    // The "Submit an extension…" link.
    Q_INVOKABLE QUrl contributingUrl() const;

    // Parses the catalog JSON; false (with `error`) when it is not one.
    bool loadCatalog(const QByteArray &json, QString *error);

    // Whether an update of `installed` is allowed without asking: the new
    // entry only asks for permissions and sites the installed one had.
    static bool isSilentUpdate(const QStringList &newMatches, const QStringList &newPermissions,
                               const QStringList &oldMatches, const QStringList &oldPermissions);

signals:
    void stateChanged();
    void installingChanged();
    void installErrorChanged();
    // An update check finished (tests and the UI can follow it).
    void updatesChecked();

private:
    struct Entry {
        QString id;
        QJsonObject json;
        QString version;
        QStringList matches;
        QStringList permissions;
        QUrl package;
        QString sha256;
        qint64 size = 0;
        QString iconSource;
    };

    void setState(const QString &state, const QString &error = QString());
    void setInstalling(const QString &id);
    void setInstallError(const QString &error);
    const Entry *find(const QString &id) const;
    // Downloads and verifies the entry's package into a temporary file; the
    // callback gets its path, or an empty path and a message.
    void fetchPackage(const Entry &entry, std::function<void(const QString &, const QString &)> done);
    void applyUpdates();
    void emitAllChanged();

    QNetworkAccessManager m_network;
    QList<Entry> m_entries;
    QString m_state = QStringLiteral("idle");
    QString m_error;
    QString m_installingId;
    QString m_installError;
    QUrl m_catalogUrl;
    QUrl m_loadedFrom;
    QTimer m_updateTimer;
    QPointer<QNetworkReply> m_refreshReply;
    QStringList m_updating;
};
