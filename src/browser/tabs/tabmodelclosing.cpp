#include "browser/tabs/tabmodel.h"

#include "browser/profile/profilemanager.h"
#include "browser/tabs/tab.h"

void TabModel::rememberClosed(int index)
{
    const Tab *closing = m_tabs.at(index);
    if (closing->isPrivate() || closing->newTabPage())
        return;
    const bool wasEmpty = m_closed.isEmpty();
    m_closed.remember(closing->url(), closing->title(), index);
    if (wasEmpty)
        emit canReopenClosedTabChanged();
    emit recentlyClosedChanged();
}

Tab *TabModel::removeRow(int index)
{
    beginRemoveRows(QModelIndex(), index, index);
    Tab *tab = m_tabs.takeAt(index);
    endRemoveRows();
    emit countChanged();
    emit pinnedCountChanged();
    return tab;
}

void TabModel::fixCurrentAfterRemoval(int removedIndex)
{
    if (m_currentIndex > removedIndex)
        --m_currentIndex;
    else if (m_currentIndex == removedIndex)
        m_currentIndex = m_tabs.isEmpty() ? -1 : qMin(removedIndex, count() - 1);
    else
        return;
    notifyCurrentChanged();
}

void TabModel::closeTab(int index)
{
    if (!isValidIndex(index))
        return;
    rememberClosed(index);
    Tab *tab = removeRow(index);
    fixCurrentAfterRemoval(index);
    tab->deleteLater();
}

void TabModel::closeTabObject(Tab *tab)
{
    const int index = indexOfTab(tab);
    if (index >= 0)
        closeTab(index);
}

void TabModel::reopenClosedTab()
{
    reopenClosedTab(0);
}

void TabModel::reopenClosedTab(int index)
{
    if (index < 0 || index >= m_closed.size())
        return;
    const ClosedTab closed = m_closed.take(index);
    const int row = qBound(pinnedCount(), closed.index, count());
    Tab *tab = insertTab({row, ProfileManager::instance()->defaultProfile(), closed.url, true});
    if (!closed.title.isEmpty())
        tab->setTitle(closed.title);
    if (m_closed.isEmpty())
        emit canReopenClosedTabChanged();
    emit recentlyClosedChanged();
}

void TabModel::closeOtherTabs(int index)
{
    if (!isValidIndex(index))
        return;
    const Tab *kept = m_tabs.at(index);
    const QList<Tab *> snapshot = m_tabs;
    for (auto it = snapshot.crbegin(); it != snapshot.crend(); ++it) {
        if (*it != kept && !(*it)->pinned())
            closeTabObject(*it);
    }
}

void TabModel::closeTabsToTheRight(int index)
{
    if (!isValidIndex(index))
        return;
    for (int i = count() - 1; i > index; --i) {
        if (!m_tabs.at(i)->pinned())
            closeTab(i);
    }
}
