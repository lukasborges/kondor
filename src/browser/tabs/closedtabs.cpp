#include "browser/tabs/closedtabs.h"

#include <QVariantMap>

void ClosedTabs::remember(const QUrl &url, const QString &title, int index)
{
    m_tabs.append({url, title, index});
    while (m_tabs.size() > kMaxClosedTabs)
        m_tabs.removeFirst();
}

ClosedTab ClosedTabs::take(int indexFromNewest)
{
    return m_tabs.takeAt(m_tabs.size() - 1 - indexFromNewest);
}

QVariantList ClosedTabs::toVariantList() const
{
    QVariantList list;
    for (auto it = m_tabs.crbegin(); it != m_tabs.crend(); ++it)
        list.append(QVariantMap{{QStringLiteral("url"), it->url},
                                {QStringLiteral("title"), it->title}});
    return list;
}
