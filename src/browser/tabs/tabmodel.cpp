#include "browser/tabs/tabmodel.h"

#include "browser/tabs/assignandnotify.h"
#include "browser/profile/profilemanager.h"
#include "browser/tabs/tab.h"

#include <QQuickWebEngineProfile>

#include <algorithm>

TabModel::TabModel(QObject *parent)
    : QAbstractListModel(parent)
{
}

int TabModel::rowCount(const QModelIndex &parent) const
{
    return parent.isValid() ? 0 : count();
}

QVariant TabModel::data(const QModelIndex &index, int role) const
{
    if (!index.isValid() || !isValidIndex(index.row()) || role != TabRole)
        return {};
    return QVariant::fromValue(m_tabs.at(index.row()));
}

QHash<int, QByteArray> TabModel::roleNames() const
{
    return {{TabRole, "tab"}};
}

bool TabModel::isValidIndex(int index) const
{
    return index >= 0 && index < count();
}

Tab *TabModel::currentTab() const
{
    return isValidIndex(m_currentIndex) ? m_tabs.at(m_currentIndex) : nullptr;
}

int TabModel::pinnedCount() const
{
    return int(std::count_if(m_tabs.cbegin(), m_tabs.cend(),
                             [](const Tab *tab) { return tab->pinned(); }));
}

int TabModel::pinnedCountExcluding(int index) const
{
    return pinnedCount() - (m_tabs.at(index)->pinned() ? 1 : 0);
}

void TabModel::notifyCurrentChanged()
{
    emit currentIndexChanged();
    emit currentTabChanged();
}

QQuickWebEngineProfile *TabModel::profileFor(QQuickWebEngineProfile *requested) const
{
    auto *profiles = ProfileManager::instance();
    QQuickWebEngineProfile *profile = requested ? requested : profiles->defaultProfile();
    if (m_privateTabs && !profile->isOffTheRecord())
        return profiles->createPrivateProfile();
    return profile;
}

void TabModel::insertRow(int index, Tab *tab)
{
    beginInsertRows(QModelIndex(), index, index);
    m_tabs.insert(index, tab);
    endInsertRows();
    emit countChanged();
    emit pinnedCountChanged();
}

Tab *TabModel::insertTab(const NewTab &newTab)
{
    auto *tab = new Tab(profileFor(newTab.profile), this);
    tab->setUrl(newTab.url);
    const int index = qBound(0, newTab.index, count());
    insertRow(index, tab);
    keepCurrentWhenInsertedBefore(index);
    if (newTab.activate)
        setCurrentIndex(index);
    return tab;
}

void TabModel::keepCurrentWhenInsertedBefore(int index)
{
    if (m_currentIndex < index)
        return;
    ++m_currentIndex;
    notifyCurrentChanged();
}

Tab *TabModel::addTab(bool isPrivate, const QUrl &initialUrl)
{
    auto *profiles = ProfileManager::instance();
    const bool needsPrivateProfile = isPrivate || m_privateTabs;
    QQuickWebEngineProfile *profile = needsPrivateProfile ? profiles->createPrivateProfile()
                                                          : profiles->defaultProfile();
    return insertTab({count(), profile, initialUrl, true});
}

int TabModel::childTabRow() const
{
    const Tab *current = currentTab();
    if (!current)
        return count();
    return current->pinned() ? pinnedCount() : m_currentIndex + 1;
}

Tab *TabModel::addTabWithProfile(QQuickWebEngineProfile *profile, const QUrl &url, bool background)
{
    return insertTab({childTabRow(), profile, url, !background});
}

int TabModel::indexOfTab(Tab *tab) const
{
    return int(m_tabs.indexOf(tab));
}

void TabModel::followCurrentTab(Tab *current)
{
    if (!current)
        return;
    const int newIndex = indexOfTab(current);
    if (newIndex == m_currentIndex)
        return;
    m_currentIndex = newIndex;
    notifyCurrentChanged();
}

void TabModel::moveTab(int from, int to)
{
    if (!isValidIndex(from) || !isValidIndex(to) || from == to)
        return;
    Tab *current = currentTab();
    beginMoveRows(QModelIndex(), from, from, QModelIndex(), to > from ? to + 1 : to);
    m_tabs.move(from, to);
    endMoveRows();
    followCurrentTab(current);
}

void TabModel::duplicateTab(int index)
{
    if (!isValidIndex(index))
        return;
    const Tab *source = m_tabs.at(index);
    Tab *copy = insertTab({index + 1, source->profile(), source->url(), true});
    if (source->pinned())
        setPinned(indexOfTab(copy), true);
}

void TabModel::setPinned(int index, bool pinned)
{
    if (!isValidIndex(index) || m_tabs.at(index)->pinned() == pinned)
        return;
    m_tabs.at(index)->setPinned(pinned);
    const int target = pinnedCountExcluding(index);
    if (index != target)
        moveTab(index, target);
    emit pinnedCountChanged();
}

void TabModel::setCurrentIndex(int index)
{
    if (!isValidIndex(index) || index == m_currentIndex)
        return;
    m_currentIndex = index;
    notifyCurrentChanged();
}

void TabModel::setPrivateTabs(bool privateTabs)
{
    assignAndNotify(m_privateTabs, privateTabs, [this] { emit privateTabsChanged(); });
}
