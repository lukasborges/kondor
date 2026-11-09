#include "tabmodel.h"

#include "profilemanager.h"
#include "tab.h"

#include <QQuickWebEngineProfile>

namespace {
constexpr int kMaxClosedTabs = 20;
} // namespace

TabModel::TabModel(QObject *parent)
    : QAbstractListModel(parent)
{
}

int TabModel::rowCount(const QModelIndex &parent) const
{
    return parent.isValid() ? 0 : int(m_tabs.size());
}

QVariant TabModel::data(const QModelIndex &index, int role) const
{
    if (!index.isValid() || index.row() < 0 || index.row() >= m_tabs.size())
        return {};
    if (role == TabRole)
        return QVariant::fromValue(m_tabs.at(index.row()));
    return {};
}

QHash<int, QByteArray> TabModel::roleNames() const
{
    return {{TabRole, "tab"}};
}

Tab *TabModel::currentTab() const
{
    if (m_currentIndex < 0 || m_currentIndex >= m_tabs.size())
        return nullptr;
    return m_tabs.at(m_currentIndex);
}

int TabModel::pinnedCount() const
{
    int count = 0;
    for (const Tab *tab : m_tabs) {
        if (tab->pinned())
            ++count;
    }
    return count;
}

Tab *TabModel::insertTab(int index, QQuickWebEngineProfile *profile, const QUrl &url, bool activate)
{
    auto *profiles = ProfileManager::instance();
    if (!profile)
        profile = profiles->defaultProfile();

    index = qBound(0, index, int(m_tabs.size()));

    auto *tab = new Tab(profile, this);
    const QUrl targetUrl = url.isEmpty() ? QUrl(profiles->homePage()) : url;
    tab->setUrl(targetUrl);

    beginInsertRows(QModelIndex(), index, index);
    m_tabs.insert(index, tab);
    endInsertRows();
    emit countChanged();
    emit pinnedCountChanged();

    // Keep the same tab selected when another one is inserted before it.
    if (m_currentIndex >= index) {
        ++m_currentIndex;
        emit currentIndexChanged();
        emit currentTabChanged();
    }

    if (activate)
        setCurrentIndex(index);

    return tab;
}

Tab *TabModel::addTab(bool isPrivate, const QUrl &initialUrl)
{
    auto *profiles = ProfileManager::instance();
    QQuickWebEngineProfile *profile =
        isPrivate ? profiles->createPrivateProfile() : profiles->defaultProfile();
    return insertTab(int(m_tabs.size()), profile, initialUrl, true);
}

Tab *TabModel::addTabWithProfile(QQuickWebEngineProfile *profile, const QUrl &url, bool background)
{
    // Child tabs open right after the tab that created them, like Firefox. An
    // unpinned child of a pinned tab goes after the pinned group instead.
    int row = int(m_tabs.size());
    if (m_currentIndex >= 0 && m_currentIndex < m_tabs.size())
        row = m_tabs.at(m_currentIndex)->pinned() ? pinnedCount() : m_currentIndex + 1;
    return insertTab(row, profile, url, !background);
}

int TabModel::indexOfTab(Tab *tab) const
{
    return int(m_tabs.indexOf(tab));
}

void TabModel::closeTab(int index)
{
    if (index < 0 || index >= m_tabs.size())
        return;

    Tab *closing = m_tabs.at(index);
    if (!closing->isPrivate()) {
        m_closed.append({closing->url(), closing->title(), index});
        while (m_closed.size() > kMaxClosedTabs)
            m_closed.removeFirst();
        if (m_closed.size() == 1)
            emit canReopenClosedTabChanged();
    }

    beginRemoveRows(QModelIndex(), index, index);
    Tab *tab = m_tabs.takeAt(index);
    endRemoveRows();
    emit countChanged();
    emit pinnedCountChanged();

    if (m_currentIndex > index) {
        --m_currentIndex;
        emit currentIndexChanged();
        emit currentTabChanged();
    } else if (m_currentIndex == index) {
        if (m_tabs.isEmpty())
            m_currentIndex = -1;
        else
            m_currentIndex = qMin(index, int(m_tabs.size()) - 1);
        emit currentIndexChanged();
        emit currentTabChanged();
    }

    // The QML view is destroyed in endRemoveRows; the Tab can go afterwards.
    tab->deleteLater();
}

void TabModel::closeTabObject(Tab *tab)
{
    const int idx = m_tabs.indexOf(tab);
    if (idx >= 0)
        closeTab(idx);
}

void TabModel::reopenClosedTab()
{
    if (m_closed.isEmpty())
        return;

    const ClosedTab closed = m_closed.takeLast();

    // A reopened tab is never pinned, so it cannot land inside the pinned group.
    const int index = qBound(pinnedCount(), closed.index, int(m_tabs.size()));
    Tab *tab = insertTab(index, ProfileManager::instance()->defaultProfile(), closed.url, true);
    if (tab && !closed.title.isEmpty())
        tab->setTitle(closed.title);

    if (m_closed.isEmpty())
        emit canReopenClosedTabChanged();
}

void TabModel::moveTab(int from, int to)
{
    if (from < 0 || from >= m_tabs.size() || to < 0 || to >= m_tabs.size() || from == to)
        return;

    Tab *current = currentTab();

    // Qt expects the destination row as it is before the source row is removed.
    beginMoveRows(QModelIndex(), from, from, QModelIndex(), to > from ? to + 1 : to);
    m_tabs.move(from, to);
    endMoveRows();

    if (current) {
        const int newIndex = int(m_tabs.indexOf(current));
        if (newIndex != m_currentIndex) {
            m_currentIndex = newIndex;
            emit currentIndexChanged();
            emit currentTabChanged();
        }
    }
}

void TabModel::duplicateTab(int index)
{
    if (index < 0 || index >= m_tabs.size())
        return;

    Tab *source = m_tabs.at(index);
    Tab *copy = insertTab(index + 1, source->profile(), source->url(), true);
    if (source->pinned())
        setPinned(indexOfTab(copy), true);
}

void TabModel::closeOtherTabs(int index)
{
    if (index < 0 || index >= m_tabs.size())
        return;

    // Pinned tabs are protected and stay open.
    for (int i = int(m_tabs.size()) - 1; i >= 0; --i) {
        if (i == index || m_tabs.at(i)->pinned())
            continue;
        closeTab(i);
        if (i < index)
            --index;
    }
}

void TabModel::closeTabsToTheRight(int index)
{
    if (index < 0 || index >= m_tabs.size())
        return;

    for (int i = int(m_tabs.size()) - 1; i > index; --i) {
        if (!m_tabs.at(i)->pinned())
            closeTab(i);
    }
}

void TabModel::setPinned(int index, bool pinned)
{
    if (index < 0 || index >= m_tabs.size())
        return;

    Tab *tab = m_tabs.at(index);
    if (tab->pinned() == pinned)
        return;

    tab->setPinned(pinned);

    // Pinned tabs live at the start of the model. The tab goes to the end of
    // the pinned group when pinned and to the start of the rest when unpinned.
    int target = 0;
    for (int i = 0; i < m_tabs.size(); ++i) {
        if (i != index && m_tabs.at(i)->pinned())
            ++target;
    }

    if (index != target)
        moveTab(index, target);

    emit pinnedCountChanged();
}

void TabModel::setCurrentIndex(int index)
{
    if (index < 0 || index >= m_tabs.size() || index == m_currentIndex)
        return;
    m_currentIndex = index;
    emit currentIndexChanged();
    emit currentTabChanged();
}
