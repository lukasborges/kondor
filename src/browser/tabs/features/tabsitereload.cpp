#include "browser/tabs/features/tabsitereload.h"

TabSiteReload::TabSiteReload(QObject *parent)
    : QObject(parent)
{
}

QString TabSiteReload::extensionName() const
{
    return m_changes.isEmpty() ? QString() : m_changes.last().extensionName;
}

bool TabSiteReload::willRun() const
{
    return !m_changes.isEmpty() && m_changes.last().isEnabled;
}

qsizetype TabSiteReload::indexOf(const QString &extensionId) const
{
    for (qsizetype index = 0; index < m_changes.size(); ++index)
        if (m_changes.at(index).extensionId == extensionId)
            return index;
    return -1;
}

void TabSiteReload::update(qsizetype index, bool isEnabled)
{
    Change change = m_changes.takeAt(index);
    change.isEnabled = isEnabled;
    if (change.isEnabled != change.wasEnabled)
        m_changes.append(change);
}

void TabSiteReload::recordToggle(const QString &extensionId, const QString &extensionName,
                                 bool isEnabled)
{
    const qsizetype index = indexOf(extensionId);
    if (index < 0)
        m_changes.append({extensionId, extensionName, !isEnabled, isEnabled});
    else
        update(index, isEnabled);
    emit changed();
}

void TabSiteReload::dismiss()
{
    if (m_changes.isEmpty())
        return;
    m_changes.clear();
    emit changed();
}
