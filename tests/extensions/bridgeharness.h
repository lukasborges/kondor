#pragma once

#include <memory>

#include "extensionsharness.h"
#include "extensions/extensionbridge.h"

struct BridgeClient {
    ExtensionBridge *bridge;
    QString id;
    QString token;

    QJsonObject call(const QString &method, const QJsonArray &args = {}) const
    {
        return QJsonDocument::fromJson(bridge->request({id, token, method, args}).toUtf8()).object();
    }

    bool isOk(const QString &method, const QJsonArray &args = {}) const
    {
        return call(method, args).value(QStringLiteral("ok")).toBool();
    }
};

inline QString tokenOf(const QString &id)
{
    const QString source = ExtensionManager::instance()->scriptSource(id, 0, true);
    const QString marker = QStringLiteral("\"token\":\"");
    const int start = source.indexOf(marker);
    if (start < 0)
        return QString();
    const int from = start + marker.size();
    return source.mid(from, source.indexOf(QLatin1Char('"'), from) - from);
}

inline QString sampleToken()
{
    return tokenOf(QStringLiteral("sample"));
}

inline QString errorOf(const QJsonObject &reply)
{
    return reply.value(QStringLiteral("error")).toString();
}

struct BridgeFixture {
    std::unique_ptr<Tab> tab;
    std::unique_ptr<ExtensionBridge> bridge;

    void create()
    {
        tab.reset(new Tab(nullptr));
        bridge.reset(new ExtensionBridge);
        bridge->setTab(tab.get());
    }

    void destroy()
    {
        bridge.reset();
        tab.reset();
    }

    BridgeClient client() const
    {
        return {bridge.get(), QStringLiteral("sample"), sampleToken()};
    }
};
