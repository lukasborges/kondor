#pragma once

#include <QHash>
#include <QObject>
#include <QStringList>
#include <QTimer>
#include <QUrl>
#include <QVariantList>
#include <QVariantMap>
#include <QList>
#include <QtQmlIntegration/qqmlintegration.h>

#include "passwordimport.h"

class QQmlEngine;
class QJSEngine;

namespace KWallet {
class Wallet;
}

// QML singleton `PasswordStore`: saved logins, kept only in KWallet (folder
// "Kondor", one map per origin: username -> password). Kondor itself never
// writes a password to disk. The wallet opens lazily on first use; this class
// keeps just origins and usernames in memory, and reads a password from the
// wallet when it is needed.
class PasswordStore : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    // "closed" (not opened yet), "opening", "open" or "unavailable" (KWallet
    // disabled or access denied).
    Q_PROPERTY(QString state READ state NOTIFY stateChanged)
    // `{ origin, host, username }` per saved login. No passwords.
    Q_PROPERTY(QVariantList entries READ entries NOTIFY changed)

public:
    static PasswordStore *instance();
    static PasswordStore *create(QQmlEngine *engine, QJSEngine *jsEngine);

    // Origin ("https://host[:port]") of a page URL; empty for other schemes.
    Q_INVOKABLE static QString originOf(const QUrl &url);
    // Passwords are only offered for https: origins and localhost.
    Q_INVOKABLE static bool canSaveFor(const QString &origin);
    // Origin for what a user typed as a site ("example.com", "https://a.b/x"):
    // trimmed, "https://" added when there is no "://"; empty unless passwords
    // can be saved for the result.
    Q_INVOKABLE static QString originFromInput(const QString &text);
    Q_INVOKABLE static QString hostOfOrigin(const QString &origin);

    QString state() const;
    bool isOpen() const { return m_state == State::Open; }
    QVariantList entries() const;

    // Starts opening the wallet if that has not happened yet.
    Q_INVOKABLE void ensureOpen();
    // Forgets a failed attempt and opens the wallet again.
    Q_INVOKABLE void retry();

    // Usernames saved for an origin (empty while the wallet is not open).
    QStringList usernames(const QString &origin) const;
    // Password of one login; read from the wallet at this moment.
    Q_INVOKABLE QString password(const QString &origin, const QString &username) const;
    // `[{ username, password }]` for an origin.
    QVariantList credentialsFor(const QString &origin) const;

    // True when a login for this origin and username is already saved.
    Q_INVOKABLE bool contains(const QString &origin, const QString &username) const;

    Q_INVOKABLE bool save(const QString &origin, const QString &username, const QString &password);
    // Deletes a login from the wallet at once.
    Q_INVOKABLE void remove(const QString &origin, const QString &username);
    // Copies the password to the clipboard and clears it after 30 seconds if
    // the clipboard still holds it.
    Q_INVOKABLE void copyPassword(const QString &origin, const QString &username);

    // Import from a CSV file. The parsed logins stay in C++ (m_pendingImport)
    // and are never handed to QML. prepareImport() reads and parses the file and
    // returns `{ fileName, format, newCount, identicalCount, conflictCount,
    // conflictSites, skippedNoSite, skippedNoCredentials, skippedNotLogin,
    // error }`; error is "", "unreadable", "tooLarge", "notPasswordExport",
    // "empty" or "walletUnavailable".
    Q_INVOKABLE QVariantMap prepareImport(const QUrl &file);
    // Writes the new logins (and the conflicting ones when asked). Returns the
    // number written, or -1 when a write failed. Always drops the pending import.
    Q_INVOKABLE int commitImport(bool replaceConflicts);
    Q_INVOKABLE void cancelImport();
    // Moves the exported file to the trash; true on success.
    Q_INVOKABLE bool moveImportFileToTrash(const QUrl &file);

    // Set once the "wallet unavailable" notice was shown in a tab, so it is
    // not repeated for every login.
    bool unavailableNoticeShown() const { return m_noticeShown; }
    void setUnavailableNoticeShown() { m_noticeShown = true; }

signals:
    void stateChanged();
    // The saved logins or the wallet state changed.
    void changed();

private:
    enum class State { Closed, Opening, Open, Unavailable };

    explicit PasswordStore(QObject *parent = nullptr);
    void setState(State state);
    void onWalletOpened(bool success);
    void reloadUsernames();
    void clearClipboardIfStillHolds();
    void closeWallet();

    State m_state = State::Closed;
    KWallet::Wallet *m_wallet = nullptr;
    QHash<QString, QStringList> m_usernames;
    bool m_noticeShown = false;
    QTimer m_clipboardTimer;
    QString m_copiedPassword;
    QList<PasswordImport::Login> m_pendingImport;
};
