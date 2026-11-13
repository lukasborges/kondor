#pragma once

#include <QHash>
#include <QObject>
#include <QStringList>
#include <QUrl>
#include <QVariantList>
#include <QVariantMap>
#include <QList>
#include <QtQmlIntegration/qqmlintegration.h>

#include <optional>

#include "passwords/import/importcommit.h"
#include "passwords/import/importoutcome.h"
#include "passwords/import/importpreparation.h"
#include "passwords/passwordclipboard.h"
#include "passwords/csv/passwordimport.h"
#include "passwords/walletfolder.h"

class QQmlEngine;
class QJSEngine;

namespace KWallet {
class Wallet;
}

class PasswordStore : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    Q_PROPERTY(QString state READ state NOTIFY stateChanged)
    Q_PROPERTY(QVariantList entries READ entries NOTIFY changed)
    Q_PROPERTY(bool importPreparing READ isImportPreparing NOTIFY importPreparingChanged)
    Q_PROPERTY(bool importRunning READ isImportRunning NOTIFY importRunningChanged)
    Q_PROPERTY(int importDone READ importDone NOTIFY importDoneChanged)
    Q_PROPERTY(int importTotal READ importTotal NOTIFY importTotalChanged)

public:
    static PasswordStore *instance();
    static PasswordStore *create(QQmlEngine *engine, QJSEngine *jsEngine);

    Q_INVOKABLE static QString originOf(const QUrl &url);
    Q_INVOKABLE static bool canSaveFor(const QString &origin);
    Q_INVOKABLE static QString originFromInput(const QString &text);
    Q_INVOKABLE static QString hostOfOrigin(const QString &origin);

    QString state() const;
    bool isOpen() const { return m_state == State::Open; }
    QVariantList entries() const;

    Q_INVOKABLE void ensureOpen();
    Q_INVOKABLE void retry();

    QStringList usernames(const QString &origin) const;
    Q_INVOKABLE QString password(const QString &origin, const QString &username) const;
    QVariantList credentialsFor(const QString &origin) const;

    Q_INVOKABLE bool contains(const QString &origin, const QString &username) const;

    Q_INVOKABLE bool save(const QString &origin, const QString &username, const QString &password);
    Q_INVOKABLE void remove(const QString &origin, const QString &username);
    Q_INVOKABLE void copyPassword(const QString &origin, const QString &username);

    Q_INVOKABLE void prepareImport(const QUrl &file);
    Q_INVOKABLE void commitImport(bool replaceConflicts);
    Q_INVOKABLE void cancelImport();
    Q_INVOKABLE void setImportPageOpen(bool isOpen);
    Q_INVOKABLE QVariantMap takeImportResult();
    Q_INVOKABLE QVariantMap claimImportNotification();
    bool isImportPreparing() const { return m_preparation.isRunning(); }
    bool isImportRunning() const { return m_commit != nullptr; }
    int importDone() const { return m_commit ? m_commit->done() : 0; }
    int importTotal() const { return m_commit ? m_commit->total() : 0; }
    Q_INVOKABLE bool moveImportFileToTrash(const QUrl &file);

    bool unavailableNoticeShown() const { return m_noticeShown; }
    void setUnavailableNoticeShown() { m_noticeShown = true; }

signals:
    void stateChanged();
    void changed();
    void importPreparingChanged();
    void importRunningChanged();
    void importDoneChanged();
    void importTotalChanged();
    void importPrepared(const QVariantMap &info);
    void importFinished(int written);

private:
    enum class State { Closed, Opening, Open, Unavailable };

    explicit PasswordStore(QObject *parent = nullptr);
    void setState(State state);
    void openWallet();
    void connectWalletSignals();
    void forgetClosedWallet();
    void onWalletOpened(bool success);
    void reloadUsernames();
    void rememberUsernames(const QString &origin, const std::optional<QMap<QString, QString>> &logins);
    void notifyLoginsChanged();
    void startImportCommit(bool replaceConflicts);
    void finishImportCommit(int written);
    void emitImportProgressChanged();
    std::optional<SavedLogins> importSavedLogins() const;
    bool writeImportedLogins(const QString &origin, const QMap<QString, QString> &logins) const;
    void closeWallet();
    std::optional<WalletFolder> walletFolder() const;
    std::optional<WalletFolder> openFolder() const;

    State m_state = State::Closed;
    KWallet::Wallet *m_wallet = nullptr;
    QHash<QString, QStringList> m_usernames;
    bool m_noticeShown = false;
    PasswordClipboard m_clipboard;
    ImportPreparation m_preparation;
    ImportCommit *m_commit = nullptr;
    ImportOutcome m_importOutcome;
    QString m_importFileName;
};
