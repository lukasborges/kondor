#pragma once

#include <QAbstractListModel>
#include <QList>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>

class Tab;

class TabModel : public QAbstractListModel
{
    Q_OBJECT
    QML_ELEMENT

    Q_PROPERTY(int count READ count NOTIFY countChanged)
    Q_PROPERTY(int currentIndex READ currentIndex NOTIFY currentIndexChanged)
    Q_PROPERTY(Tab *currentTab READ currentTab NOTIFY currentTabChanged)

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

    Q_INVOKABLE Tab *addTab(bool isPrivate = false, const QUrl &initialUrl = QUrl());
    Q_INVOKABLE void closeTab(int index);
    Q_INVOKABLE void closeTabObject(Tab *tab);
    Q_INVOKABLE void setCurrentIndex(int index);

signals:
    void countChanged();
    void currentIndexChanged();
    void currentTabChanged();

private:
    QList<Tab *> m_tabs;
    int m_currentIndex = -1;
};
