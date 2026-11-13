#pragma once

#include <QMap>
#include <QString>
#include <QStringList>

#include <optional>

#include "passwords/csv/passwordimportplan.h"

namespace KWallet {
class Wallet;
}

class WalletFolder
{
public:
    explicit WalletFolder(KWallet::Wallet *wallet);

    static bool ensureExists(KWallet::Wallet *wallet);

    std::optional<QMap<QString, QString>> logins(const QString &origin) const;
    std::optional<SavedLogins> allLogins() const;
    bool writeLogins(const QString &origin, const QMap<QString, QString> &logins) const;
    bool removeOrigin(const QString &origin) const;
    QStringList origins() const;

private:
    void select() const;

    KWallet::Wallet *m_wallet;
};
