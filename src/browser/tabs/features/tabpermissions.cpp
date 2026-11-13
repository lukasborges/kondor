#include "browser/tabs/features/tabpermissions.h"

#include <utility>

namespace {
void resolve(const QWebEnginePermission &permission, bool grant)
{
    if (grant)
        permission.grant();
    else
        permission.deny();
}
}

TabPermissions::TabPermissions(QObject *parent)
    : QObject(parent)
{
}

QVariant TabPermissions::pending() const
{
    if (m_queue.isEmpty())
        return QVariant();
    return QVariant::fromValue(m_queue.first());
}

void TabPermissions::enqueue(const QWebEnginePermission &permission)
{
    if (!permission.isValid())
        return;
    const bool wasEmpty = m_queue.isEmpty();
    m_queue.append(permission);
    if (wasEmpty)
        emit pendingChanged();
}

bool TabPermissions::dropInvalidFront()
{
    bool dropped = false;
    while (!m_queue.isEmpty() && !m_queue.first().isValid()) {
        m_queue.removeFirst();
        dropped = true;
    }
    return dropped;
}

void TabPermissions::answer(bool grant)
{
    const bool dropped = dropInvalidFront();
    const bool hasQuestion = !m_queue.isEmpty();
    if (hasQuestion)
        resolve(m_queue.takeFirst(), grant);
    if (dropped || hasQuestion)
        emit pendingChanged();
}

void TabPermissions::denyAll()
{
    if (m_queue.isEmpty())
        return;
    for (const QWebEnginePermission &permission : std::as_const(m_queue)) {
        if (permission.isValid())
            permission.deny();
    }
    m_queue.clear();
    emit pendingChanged();
}
