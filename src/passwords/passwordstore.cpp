#include "passwords/passwordstore.h"

#include "passwords/passwordorigin.h"

#include <KWallet>

namespace {

QVariantMap entryFor(const QString &origin, const QString &username)
{
    return {
        {QStringLiteral("origin"), origin},
        {QStringLiteral("host"), PasswordOrigin::hostOfOrigin(origin)},
        {QStringLiteral("username"), username},
    };
}

QVariantList credentialList(const QMap<QString, QString> &logins)
{
    QVariantList list;
    for (auto it = logins.cbegin(); it != logins.cend(); ++it) {
        list.append(QVariantMap{
            {QStringLiteral("username"), it.key()},
            {QStringLiteral("password"), it.value()},
        });
    }
    return list;
}

QMap<QString, QString> loginsOrEmpty(const WalletFolder &folder, const QString &origin)
{
    return folder.logins(origin).value_or(QMap<QString, QString>());
}

void writeOrRemove(const WalletFolder &folder, const QString &origin, const QMap<QString, QString> &logins)
{
    if (logins.isEmpty())
        folder.removeOrigin(origin);
    else
        folder.writeLogins(origin, logins);
}

}

PasswordStore *PasswordStore::instance()
{
    static PasswordStore *store = new PasswordStore;
    return store;
}

PasswordStore *PasswordStore::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(engine)
    Q_UNUSED(jsEngine)
    return instance();
}

PasswordStore::PasswordStore(QObject *parent)
    : QObject(parent)
    , m_clipboard(this)
{
}

QString PasswordStore::originOf(const QUrl &url)
{
    return PasswordOrigin::originOf(url);
}

bool PasswordStore::canSaveFor(const QString &origin)
{
    return PasswordOrigin::canSaveFor(origin);
}

QString PasswordStore::originFromInput(const QString &text)
{
    return PasswordOrigin::originFromInput(text);
}

QString PasswordStore::hostOfOrigin(const QString &origin)
{
    return PasswordOrigin::hostOfOrigin(origin);
}

void PasswordStore::reloadUsernames()
{
    m_usernames.clear();
    const auto folder = walletFolder();
    if (!folder)
        return;
    for (const QString &origin : folder->origins())
        rememberUsernames(origin, folder->logins(origin));
}

void PasswordStore::rememberUsernames(const QString &origin,
                                      const std::optional<QMap<QString, QString>> &logins)
{
    if (!logins || logins->isEmpty())
        return;
    QStringList names = logins->keys();
    names.sort(Qt::CaseInsensitive);
    m_usernames.insert(origin, names);
}

void PasswordStore::notifyLoginsChanged()
{
    reloadUsernames();
    emit changed();
}

QVariantList PasswordStore::entries() const
{
    QVariantList list;
    for (auto it = m_usernames.cbegin(); it != m_usernames.cend(); ++it) {
        for (const QString &name : it.value())
            list.append(entryFor(it.key(), name));
    }
    return list;
}

QStringList PasswordStore::usernames(const QString &origin) const
{
    return m_usernames.value(origin);
}

bool PasswordStore::contains(const QString &origin, const QString &username) const
{
    return usernames(origin).contains(username);
}

QString PasswordStore::password(const QString &origin, const QString &username) const
{
    const auto folder = openFolder();
    if (!folder)
        return {};
    return loginsOrEmpty(*folder, origin).value(username);
}

QVariantList PasswordStore::credentialsFor(const QString &origin) const
{
    const auto folder = openFolder();
    if (!folder || !m_usernames.contains(origin))
        return {};
    return credentialList(loginsOrEmpty(*folder, origin));
}

bool PasswordStore::save(const QString &origin, const QString &username, const QString &password)
{
    const auto folder = openFolder();
    if (!folder || origin.isEmpty())
        return false;
    QMap<QString, QString> logins = loginsOrEmpty(*folder, origin);
    logins.insert(username, password);
    if (!folder->writeLogins(origin, logins))
        return false;
    notifyLoginsChanged();
    return true;
}

void PasswordStore::remove(const QString &origin, const QString &username)
{
    const auto folder = openFolder();
    if (!folder)
        return;
    auto logins = folder->logins(origin);
    if (!logins || !logins->contains(username))
        return;
    logins->remove(username);
    writeOrRemove(*folder, origin, *logins);
    notifyLoginsChanged();
}

void PasswordStore::copyPassword(const QString &origin, const QString &username)
{
    const QString secret = password(origin, username);
    if (!secret.isEmpty())
        m_clipboard.copy(secret);
}
