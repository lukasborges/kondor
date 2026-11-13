#include "extensions/bridge/extensionpageapi.h"

#include "extensions/bridge/extensionbridge.h"
#include "extensions/bridge/extensioncall.h"

ExtensionPageApi::ExtensionPageApi(ExtensionBridge *bridge)
    : QObject(bridge)
    , m_bridge(bridge)
{
}

QString ExtensionPageApi::request(const QString &requestJson)
{
    return m_bridge->request(parseExtensionCall(requestJson));
}
