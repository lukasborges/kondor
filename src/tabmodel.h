#pragma once

#include <QAbstractListModel>
#include <QList>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>

class QQuickWebEngineProfile;
class Tab;

class TabModel : public QAbstractListModel
{
    Q_OBJECT
    QML_ELEMENT

    Q_PROPERTY(int count READ count NOTIFY countChanged)
    Q_PROPERTY(int currentIndex READ currentIndex NOTIFY currentIndexChanged)
    Q_PROPERTY(Tab *currentTab READ currentTab NOTIFY currentTabChanged)
    Q_PROPERTY(int pinnedCount READ pinnedCount NOTIFY pinnedCountChanged)
    Q_PROPERTY(bool canReopenClosedTab READ canReopenClosedTab
                   NOTIFY canReopenClosedTabChanged)

public:
    enum Roles {
        TabRole = Qt::UserRole + 1,
    };

    explicit TabModel(QObject *parent = nullptr);

    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role) const override;
    QHash<int, QByteArray> roleNames() const override;

    int count() const { return int(m_tabs.size()); }
    int currentIndex() const { return m_currentIndex; }
    Tab *currentTab() const;
    int pinnedCount() const;
    bool canReopenClosedTab() const { return !m_closed.isEmpty(); }

    Q_INVOKABLE Tab *insertTab(int index, QQuickWebEngineProfile *profile, const QUrl &url, bool activate);
    Q_INVOKABLE Tab *addTab(bool isPrivate = false, const QUrl &initialUrl = QUrl());
    Q_INVOKABLE Tab *addTabWithProfile(QQuickWebEngineProfile *profile, const QUrl &url, bool background);
    Q_INVOKABLE int indexOfTab(Tab *tab) const;
    Q_INVOKABLE void closeTab(int index);
    Q_INVOKABLE void closeTabObject(Tab *tab);
    Q_INVOKABLE void reopenClosedTab();
    Q_INVOKABLE void moveTab(int from, int to);
    Q_INVOKABLE void duplicateTab(int index);
    Q_INVOKABLE void closeOtherTabs(int index);
    Q_INVOKABLE void closeTabsToTheRight(int index);
    Q_INVOKABLE void setPinned(int index, bool pinned);
    Q_INVOKABLE void setCurrentIndex(int index);

signals:
    void countChanged();
    void currentIndexChanged();
    void currentTabChanged();
    void pinnedCountChanged();
    void canReopenClosedTabChanged();

private:
    struct ClosedTab {
        QUrl url;
        QString title;
        int index = 0;
    };

    QList<Tab *> m_tabs;
    // Last closed normal tabs, oldest first; private tabs are never kept.
    QList<ClosedTab> m_closed;
    int m_currentIndex = -1;
};
