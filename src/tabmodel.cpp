#include "tabmodel.h"

#include "profilemanager.h"
#include "tab.h"

#include <QQuickWebEngineProfile>

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

Tab *TabModel::addTab(bool isPrivate, const QUrl &initialUrl)
{
    auto *profiles = ProfileManager::instance();
    QQuickWebEngineProfile *profile =
        isPrivate ? profiles->createPrivateProfile() : profiles->defaultProfile();

    auto *tab = new Tab(profile, this);
    const QUrl url = initialUrl.isEmpty() ? QUrl(profiles->homePage()) : initialUrl;
    tab->setUrl(url);

    const int row = int(m_tabs.size());
    beginInsertRows(QModelIndex(), row, row);
    m_tabs.append(tab);
    endInsertRows();
    emit countChanged();

    setCurrentIndex(row);
    return tab;
}

void TabModel::closeTab(int index)
{
    if (index < 0 || index >= m_tabs.size())
        return;

    beginRemoveRows(QModelIndex(), index, index);
    Tab *tab = m_tabs.takeAt(index);
    endRemoveRows();
    emit countChanged();

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

    // A view QML é destruída em endRemoveRows; o Tab pode ir depois.
    tab->deleteLater();
}

void TabModel::closeTabObject(Tab *tab)
{
    const int idx = m_tabs.indexOf(tab);
    if (idx >= 0)
        closeTab(idx);
}

void TabModel::setCurrentIndex(int index)
{
    if (index < 0 || index >= m_tabs.size() || index == m_currentIndex)
        return;
    m_currentIndex = index;
    emit currentIndexChanged();
    emit currentTabChanged();
}
