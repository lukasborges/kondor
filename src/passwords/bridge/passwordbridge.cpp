#include "passwords/passwordbridge.h"

#include "passwords/passwordstore.h"
#include "core/settings.h"
#include "browser/tab.h"
#include "browser/tabpasswords.h"

PasswordPageApi::PasswordPageApi(PasswordBridge *bridge)
    : QObject(bridge)
    , m_bridge(bridge)
{
}

void PasswordPageApi::formSubmitted(const QString &origin, const QString &username,
                                    const QString &password)
{
    m_bridge->formSubmitted(origin, username, password);
}

QVariantList PasswordPageApi::credentialsFor(const QString &origin)
{
    return m_bridge->credentialsFor(origin);
}

PasswordBridge::PasswordBridge(QObject *parent)
    : QObject(parent)
    , m_api(new PasswordPageApi(this))
{
    connect(PasswordStore::instance(), &PasswordStore::changed, m_api,
            &PasswordPageApi::credentialsChanged);
}

void PasswordBridge::setTab(Tab *tab)
{
    if (m_tab == tab)
        return;
    m_tab = tab;
    emit tabChanged();
}

bool PasswordBridge::allowed() const
{
    return m_tab && !m_tab->isPrivate();
}

bool PasswordBridge::mayOfferSave(const QString &origin, const QString &password) const
{
    if (!allowed() || password.isEmpty() || !PasswordStore::canSaveFor(origin))
        return false;
    Settings *settings = Settings::instance();
    return settings->offerToSavePasswords() && !settings->passwordNeverSaveSites().contains(origin);
}

void PasswordBridge::showWalletNoticeOnce()
{
    PasswordStore *store = PasswordStore::instance();
    if (store->unavailableNoticeShown())
        return;
    store->setUnavailableNoticeShown();
    m_tab->passwords()->showWalletNotice();
}

bool PasswordBridge::isAlreadySaved(const QString &origin, const QString &username,
                                    const QString &password) const
{
    PasswordStore *store = PasswordStore::instance();
    return store->usernames(origin).contains(username) && store->password(origin, username) == password;
}

void PasswordBridge::formSubmitted(const QString &origin, const QString &username,
                                   const QString &password)
{
    if (!mayOfferSave(origin, password))
        return;
    PasswordStore *store = PasswordStore::instance();
    store->ensureOpen();
    if (store->state() == QLatin1String("unavailable"))
        showWalletNoticeOnce();
    else if (store->isOpen() && !isAlreadySaved(origin, username, password))
        m_tab->passwords()->offerSave(origin, username, password);
}

QVariantList PasswordBridge::credentialsFor(const QString &origin)
{
    if (!allowed() || origin.isEmpty())
        return {};
    PasswordStore *store = PasswordStore::instance();
    store->ensureOpen();
    return store->credentialsFor(origin);
}

void PasswordBridge::fill(const QString &username)
{
    if (!allowed())
        return;
    const QString origin = PasswordStore::originOf(m_tab->url());
    PasswordStore *store = PasswordStore::instance();
    if (origin.isEmpty() || !store->isOpen())
        return;
    emit m_api->fillRequested(origin, username, store->password(origin, username));
}
