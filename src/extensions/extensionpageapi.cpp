#include "extensions/extensionpageapi.h"

#include "extensions/extensionbridge.h"
#include "extensions/extensioncall.h"

ExtensionPageApi::ExtensionPageApi(ExtensionBridge *bridge)
    : QObject(bridge)
    , m_bridge(bridge)
{
}

QString ExtensionPageApi::request(const QString &requestJson)
{
    return m_bridge->request(parseExtensionCall(requestJson));
}
