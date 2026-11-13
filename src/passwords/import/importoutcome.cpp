#include "passwords/import/importoutcome.h"

void ImportOutcome::record(int written, const QString &fileName)
{
    m_result = {{QStringLiteral("count"), written}, {QStringLiteral("fileName"), fileName}};
    m_isNotified = false;
}

void ImportOutcome::setPageOpen(bool isOpen)
{
    m_isPageOpen = isOpen;
}

QVariantMap ImportOutcome::take()
{
    return std::exchange(m_result, {});
}

QVariantMap ImportOutcome::claimNotification()
{
    const bool isSuccess = m_result.value(QStringLiteral("count")).toInt() >= 0;
    if (m_result.isEmpty() || m_isNotified || m_isPageOpen || !isSuccess)
        return {};
    m_isNotified = true;
    return m_result;
}
