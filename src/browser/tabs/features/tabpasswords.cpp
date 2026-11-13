#include "browser/tabpasswords.h"

#include "browser/assignandnotify.h"
#include "core/settings.h"
#include "passwords/passwordstore.h"

TabPasswords::TabPasswords(bool isPrivate, QObject *parent)
    : QObject(parent)
    , m_isPrivate(isPrivate)
{
    if (!m_isPrivate)
        connect(PasswordStore::instance(), &PasswordStore::changed, this,
                [this] { updateUsernamesFor(m_url); });
}

QString TabPasswords::promptHost() const
{
    return PasswordStore::hostOfOrigin(m_origin);
}

void TabPasswords::updateUsernamesFor(const QUrl &url)
{
    m_url = url;
    QStringList names;
    if (!m_isPrivate)
        names = PasswordStore::instance()->usernames(PasswordStore::originOf(url));
    assignAndNotify(m_usernames, names, [this] { emit usernamesChanged(); });
}

void TabPasswords::clearPrompt()
{
    m_password.clear();
    m_origin.clear();
    m_username.clear();
    assignAndNotify(m_prompt, QString(), [this] { emit promptChanged(); });
}

void TabPasswords::showPrompt(const QString &prompt)
{
    m_prompt = prompt;
    emit promptChanged();
}

void TabPasswords::offerSave(const QString &origin, const QString &username,
                             const QString &password)
{
    if (m_isPrivate)
        return;
    m_origin = origin;
    m_username = username;
    m_password = password;
    showPrompt(QStringLiteral("save"));
}

void TabPasswords::showWalletNotice()
{
    if (m_isPrivate)
        return;
    m_password.clear();
    m_username.clear();
    m_origin.clear();
    showPrompt(QStringLiteral("walletUnavailable"));
}

void TabPasswords::savePending()
{
    if (m_isPrivate || m_prompt != QLatin1String("save"))
        return;
    PasswordStore::instance()->save(m_origin, m_username, m_password);
    clearPrompt();
}

void TabPasswords::addOriginToNeverSaveSites()
{
    Settings *settings = Settings::instance();
    QStringList sites = settings->passwordNeverSaveSites();
    if (sites.contains(m_origin))
        return;
    sites.append(m_origin);
    settings->setPasswordNeverSaveSites(sites);
}

void TabPasswords::neverSavePending()
{
    if (m_prompt != QLatin1String("save"))
        return;
    addOriginToNeverSaveSites();
    clearPrompt();
}

void TabPasswords::dismissPrompt()
{
    clearPrompt();
}

void TabPasswords::fill(const QString &username)
{
    if (m_isPrivate)
        return;
    emit fillRequested(username);
}
