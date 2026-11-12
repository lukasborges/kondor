#include "passwords/passwordbridge.h"

#include "passwords/passwordstore.h"
#include "core/settings.h"
#include "browser/tab.h"

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

void PasswordBridge::formSubmitted(const QString &origin, const QString &username,
                                   const QString &password)
{
    if (!allowed() || password.isEmpty() || !PasswordStore::canSaveFor(origin))
        return;
    Settings *settings = Settings::instance();
    if (!settings->offerToSavePasswords() || settings->passwordNeverSaveSites().contains(origin))
        return;

    PasswordStore *store = PasswordStore::instance();
    store->ensureOpen();
    if (store->state() == QLatin1String("unavailable")) {
        // Feature off: tell the user once, in this tab.
        if (!store->unavailableNoticeShown()) {
            store->setUnavailableNoticeShown();
            m_tab->showPasswordWalletNotice();
        }
        return;
    }
    if (!store->isOpen())
        return;
    // Already saved with this very password: nothing to offer.
    if (store->usernames(origin).contains(username) && store->password(origin, username) == password)
        return;
    m_tab->offerPasswordSave(origin, username, password);
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
