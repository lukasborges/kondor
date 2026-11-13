#pragma once

#include <QObject>
#include <QPointer>
#include <QtQmlIntegration/qqmlintegration.h>

#include "browser/tabs/tab.h"
#include "extensions/bridge/extensioncall.h"

class ExtensionPageApi;

class ExtensionBridge : public QObject
{
    Q_OBJECT
    QML_ELEMENT

    Q_PROPERTY(Tab *tab READ tab WRITE setTab NOTIFY tabChanged)

public:
    explicit ExtensionBridge(QObject *parent = nullptr);

    Tab *tab() const { return m_tab; }
    void setTab(Tab *tab);

    Q_INVOKABLE QObject *pageApi() const;

    QString request(const ExtensionCall &call);

signals:
    void tabChanged();

private:
    QString refusalFor(const ExtensionCall &call) const;

    QPointer<Tab> m_tab;
    ExtensionPageApi *m_api;
};
