#pragma once

#include <QSet>
#include <QString>

class AdBlockAllowList
{
public:
    bool isAllowed(const QString &host) const;
    void setPersistent(const QString &host, bool allowed);
    void setForSession(const QString &host, bool allowed);
    QSet<QString> hosts() const;

private:
    void allowForSession(const QString &host);
    void blockForSession(const QString &host);

    QSet<QString> m_sessionAllowed;
    QSet<QString> m_sessionBlocked;
};
