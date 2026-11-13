#pragma once

#include <QList>
#include <QObject>
#include <QString>
#include <QtQmlIntegration/qqmlintegration.h>

class TabSiteReload : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_UNCREATABLE("Owned by Tab")

    Q_PROPERTY(bool isPending READ isPending NOTIFY changed)
    Q_PROPERTY(QString extensionName READ extensionName NOTIFY changed)
    Q_PROPERTY(bool willRun READ willRun NOTIFY changed)

public:
    explicit TabSiteReload(QObject *parent = nullptr);

    bool isPending() const { return !m_changes.isEmpty(); }
    QString extensionName() const;
    bool willRun() const;

    Q_INVOKABLE void recordToggle(const QString &extensionId, const QString &extensionName,
                                  bool isEnabled);
    Q_INVOKABLE void dismiss();

signals:
    void changed();

private:
    struct Change
    {
        QString extensionId;
        QString extensionName;
        bool wasEnabled = false;
        bool isEnabled = false;
    };

    qsizetype indexOf(const QString &extensionId) const;
    void update(qsizetype index, bool isEnabled);

    QList<Change> m_changes;
};
