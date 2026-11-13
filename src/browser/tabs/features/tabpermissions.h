#pragma once

#include <QList>
#include <QObject>
#include <QVariant>
#include <QWebEnginePermission>
#include <QtQmlIntegration/qqmlintegration.h>

class TabPermissions : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_UNCREATABLE("Owned by Tab")

    Q_PROPERTY(QVariant pending READ pending NOTIFY pendingChanged)

public:
    explicit TabPermissions(QObject *parent = nullptr);

    QVariant pending() const;

    void denyAll();
    Q_INVOKABLE void enqueue(const QWebEnginePermission &permission);
    Q_INVOKABLE void answer(bool grant);

signals:
    void pendingChanged();

private:
    bool dropInvalidFront();

    QList<QWebEnginePermission> m_queue;
};
