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

#include "passwords/passwordclipboard.h"
#include "passwords/passwordimport.h"
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

    Q_INVOKABLE QVariantMap prepareImport(const QUrl &file);
    Q_INVOKABLE int commitImport(bool replaceConflicts);
    Q_INVOKABLE void cancelImport();
    Q_INVOKABLE bool moveImportFileToTrash(const QUrl &file);

    bool unavailableNoticeShown() const { return m_noticeShown; }
    void setUnavailableNoticeShown() { m_noticeShown = true; }

signals:
    void stateChanged();
    void changed();

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
    QVariantMap describeImport(const WalletFolder &folder, const QUrl &file, PasswordImport::Result &parsed);
    void closeWallet();
    std::optional<WalletFolder> walletFolder() const;
    std::optional<WalletFolder> openFolder() const;

    State m_state = State::Closed;
    KWallet::Wallet *m_wallet = nullptr;
    QHash<QString, QStringList> m_usernames;
    bool m_noticeShown = false;
    PasswordClipboard m_clipboard;
    QList<PasswordImport::Login> m_pendingImport;
};
