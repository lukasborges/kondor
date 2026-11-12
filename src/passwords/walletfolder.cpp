#include "passwords/walletfolder.h"

#include <KWallet>

namespace {
const QString kFolder = QStringLiteral("Kondor");
}

WalletFolder::WalletFolder(KWallet::Wallet *wallet)
    : m_wallet(wallet)
{
}

bool WalletFolder::ensureExists(KWallet::Wallet *wallet)
{
    return wallet->hasFolder(kFolder) || wallet->createFolder(kFolder);
}

void WalletFolder::select() const
{
    m_wallet->setFolder(kFolder);
}

std::optional<QMap<QString, QString>> WalletFolder::logins(const QString &origin) const
{
    select();
    QMap<QString, QString> map;
    if (m_wallet->readMap(origin, map) != 0)
        return std::nullopt;
    return map;
}

bool WalletFolder::writeLogins(const QString &origin, const QMap<QString, QString> &logins) const
{
    select();
    return m_wallet->writeMap(origin, logins) == 0;
}

bool WalletFolder::removeOrigin(const QString &origin) const
{
    select();
    return m_wallet->removeEntry(origin) == 0;
}

QStringList WalletFolder::origins() const
{
    select();
    return m_wallet->entryList();
}
