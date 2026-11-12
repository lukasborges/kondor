#include "passwords/passwordstore.h"

#include <KWallet>

namespace {

bool isWalletDisabledByEnvironment()
{
    return qEnvironmentVariableIntValue("KONDOR_NO_KWALLET") != 0;
}

}

QString PasswordStore::state() const
{
    static const QStringList names{QStringLiteral("closed"), QStringLiteral("opening"),
                                   QStringLiteral("open"), QStringLiteral("unavailable")};
    return names.at(int(m_state));
}

void PasswordStore::setState(State state)
{
    if (m_state == state)
        return;
    m_state = state;
    emit stateChanged();
    emit changed();
}

std::optional<WalletFolder> PasswordStore::walletFolder() const
{
    if (!m_wallet || !m_wallet->isOpen())
        return std::nullopt;
    return WalletFolder(m_wallet);
}

std::optional<WalletFolder> PasswordStore::openFolder() const
{
    if (!isOpen())
        return std::nullopt;
    return walletFolder();
}

void PasswordStore::ensureOpen()
{
    if (m_state != State::Closed)
        return;
    if (isWalletDisabledByEnvironment()) {
        setState(State::Unavailable);
        return;
    }
    setState(State::Opening);
    openWallet();
}

void PasswordStore::openWallet()
{
    m_wallet = KWallet::Wallet::openWallet(KWallet::Wallet::NetworkWallet(), 0,
                                           KWallet::Wallet::Asynchronous);
    if (m_wallet)
        connectWalletSignals();
    else
        setState(State::Unavailable);
}

void PasswordStore::connectWalletSignals()
{
    connect(m_wallet, &KWallet::Wallet::walletOpened, this, &PasswordStore::onWalletOpened);
    connect(m_wallet, &KWallet::Wallet::walletClosed, this, &PasswordStore::forgetClosedWallet);
}

void PasswordStore::forgetClosedWallet()
{
    closeWallet();
    m_usernames.clear();
    setState(State::Closed);
}

void PasswordStore::closeWallet()
{
    if (!m_wallet)
        return;
    m_wallet->disconnect(this);
    m_wallet->deleteLater();
    m_wallet = nullptr;
}

void PasswordStore::retry()
{
    if (m_state == State::Opening || m_state == State::Open)
        return;
    closeWallet();
    m_state = State::Closed;
    ensureOpen();
}

void PasswordStore::onWalletOpened(bool success)
{
    if (!success || !walletFolder() || !WalletFolder::ensureExists(m_wallet)) {
        closeWallet();
        setState(State::Unavailable);
        return;
    }
    reloadUsernames();
    setState(State::Open);
    emit changed();
}
