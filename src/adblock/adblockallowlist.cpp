#include "adblock/adblockallowlist.h"

#include "core/settings.h"

namespace {
bool isPersistent(const QString &host)
{
    return Settings::instance()->adBlockAllowList().contains(host);
}

QStringList withChoice(QStringList list, const QString &host, bool allowed)
{
    if (!allowed)
        list.removeAll(host);
    else if (!list.contains(host))
        list.append(host);
    return list;
}
}

bool AdBlockAllowList::isAllowed(const QString &host) const
{
    const QString key = host.toLower();
    if (m_sessionBlocked.contains(key))
        return false;
    return isPersistent(key) || m_sessionAllowed.contains(key);
}

void AdBlockAllowList::setPersistent(const QString &host, bool allowed)
{
    const QString key = host.toLower();
    if (key.isEmpty())
        return;
    m_sessionAllowed.remove(key);
    m_sessionBlocked.remove(key);
    const QStringList list = Settings::instance()->adBlockAllowList();
    Settings::instance()->setAdBlockAllowList(withChoice(list, key, allowed));
}

void AdBlockAllowList::setForSession(const QString &host, bool allowed)
{
    const QString key = host.toLower();
    if (key.isEmpty())
        return;
    if (allowed)
        allowForSession(key);
    else
        blockForSession(key);
}

void AdBlockAllowList::allowForSession(const QString &host)
{
    m_sessionAllowed.insert(host);
    m_sessionBlocked.remove(host);
}

void AdBlockAllowList::blockForSession(const QString &host)
{
    m_sessionAllowed.remove(host);
    if (isPersistent(host))
        m_sessionBlocked.insert(host);
}

QSet<QString> AdBlockAllowList::hosts() const
{
    const QStringList persisted = Settings::instance()->adBlockAllowList();
    QSet<QString> hosts = m_sessionAllowed;
    hosts.unite(QSet<QString>(persisted.begin(), persisted.end()));
    return hosts.subtract(m_sessionBlocked);
}
