#pragma once

#include <QString>
#include <QVariantMap>

class ImportOutcome
{
public:
    void record(int written, const QString &fileName);
    void setPageOpen(bool isOpen);
    QVariantMap take();
    QVariantMap claimNotification();

private:
    QVariantMap m_result;
    bool m_isNotified = false;
    bool m_isPageOpen = false;
};
