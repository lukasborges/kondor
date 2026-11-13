#pragma once

#include <QList>
#include <QString>
#include <QUrl>
#include <QVariantList>

struct ClosedTab
{
    QUrl url;
    QString title;
    int index = 0;
};

class ClosedTabs
{
public:
    static constexpr int kMaxClosedTabs = 20;

    void remember(const QUrl &url, const QString &title, int index);
    ClosedTab take(int indexFromNewest);
    bool isEmpty() const { return m_tabs.isEmpty(); }
    int size() const { return int(m_tabs.size()); }
    QVariantList toVariantList() const;

private:
    QList<ClosedTab> m_tabs;
};
