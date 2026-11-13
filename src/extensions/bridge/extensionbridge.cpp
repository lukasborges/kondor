#include "extensions/bridge/extensionbridge.h"

#include "extensions/bridge/bridgecalls.h"
#include "extensions/extensionmanager.h"
#include "extensions/bridge/extensionpageapi.h"

ExtensionBridge::ExtensionBridge(QObject *parent)
    : QObject(parent)
    , m_api(new ExtensionPageApi(this))
{
}

QObject *ExtensionBridge::pageApi() const
{
    return m_api;
}

void ExtensionBridge::setTab(Tab *tab)
{
    if (m_tab == tab)
        return;
    m_tab = tab;
    emit tabChanged();
}

QString ExtensionBridge::refusalFor(const ExtensionCall &call) const
{
    ExtensionManager *manager = ExtensionManager::instance();
    if (!m_tab)
        return errorReply(QStringLiteral("No tab"));
    if (!manager->checkToken(call.extensionId, call.token))
        return errorReply(QStringLiteral("Invalid extension token"));
    if (!manager->isActive(call.extensionId, m_tab->isPrivate()))
        return errorReply(QStringLiteral("The extension is turned off"));
    return QString();
}

QString ExtensionBridge::request(const ExtensionCall &call)
{
    const QString refusal = refusalFor(call);
    return refusal.isEmpty() ? handleBridgeCall({m_tab, call}) : refusal;
}
