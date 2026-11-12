#pragma once

#include <QJsonArray>
#include <QObject>
#include <QPointer>
#include <QtQmlIntegration/qqmlintegration.h>

#include "tab.h"

class ExtensionBridge;

// The only object published on the web channel as "kondorExtensions": a
// single entry point, with no property that could leak the tab or the profile.
class ExtensionPageApi : public QObject
{
    Q_OBJECT
public:
    explicit ExtensionPageApi(ExtensionBridge *bridge);

    // JSON in, JSON out: `{"ok":true,"value":...}` or `{"ok":false,"error":"..."}`.
    Q_INVOKABLE QString request(const QString &extensionId, const QString &token,
                                const QString &method, const QString &argumentsJson);

private:
    ExtensionBridge *m_bridge;
};

// Per-tab bridge of the Kondor extension API (docs/extensions/api.md). Every
// call carries the extension id and its token; the bridge rejects a wrong
// token, an extension that is off (or not allowed in a private tab) and a
// missing permission. It acts on the tab through the Tab commands.
class ExtensionBridge : public QObject
{
    Q_OBJECT
    QML_ELEMENT

    Q_PROPERTY(Tab *tab READ tab WRITE setTab NOTIFY tabChanged)

public:
    explicit ExtensionBridge(QObject *parent = nullptr);

    Tab *tab() const { return m_tab; }
    void setTab(Tab *tab);

    // The object to register on the web channel as "kondorExtensions".
    Q_INVOKABLE QObject *pageApi() const { return m_api; }

    QString request(const QString &extensionId, const QString &token, const QString &method,
                    const QString &argumentsJson);

signals:
    void tabChanged();

private:
    QPointer<Tab> m_tab;
    ExtensionPageApi *m_api;
};
