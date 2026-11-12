#pragma once

#include <QObject>
#include <QSet>
#include <QString>
#include <QtQmlIntegration/qqmlintegration.h>

class TabExtensionItems : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_UNCREATABLE("Owned by Tab")

public:
    explicit TabExtensionItems(QObject *parent = nullptr);

    Q_INVOKABLE bool isChecked(const QString &extensionId, const QString &itemId) const;
    Q_INVOKABLE void setChecked(const QString &extensionId, const QString &itemId, bool checked);
    Q_INVOKABLE void trigger(const QString &extensionId, const QString &itemId, bool checkable);

signals:
    void changed();
    void triggered(const QString &extensionId, const QString &itemId, bool checked);

private:
    static QString keyOf(const QString &extensionId, const QString &itemId);

    QSet<QString> m_checked;
};
