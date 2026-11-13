#include "extensions/bridgecalls.h"

#include <QUrl>

#include "browser/tabextensionitems.h"
#include "core/notifier.h"
#include "extensions/extensionmanager.h"
#include "extensions/extensionstorage.h"

namespace {

using Handler = QString (*)(const BridgeContext &context);
using TabCommand = void (*)(Tab &tab);

struct BridgeMethod {
    const char *name;
    const char *permission;
    Handler handler;
};

struct TabCommandEntry {
    const char *name;
    TabCommand run;
};

QString stringArgument(const BridgeContext &context, int index)
{
    return context.call.arguments.at(index).toString();
}

QString keyRefusal(const BridgeContext &context)
{
    if (context.call.arguments.at(0).isString())
        return QString();
    return errorReply(QStringLiteral("The key must be a string"));
}

QString writeRefusal(const BridgeContext &context)
{
    if (context.tab->isPrivate())
        return errorReply(QStringLiteral("Storage is read-only in private windows"));
    return keyRefusal(context);
}

bool isWebAddress(const QUrl &url)
{
    return url.isValid() && (url.scheme() == QLatin1String("http") || url.scheme() == QLatin1String("https"));
}

QString storageGet(const BridgeContext &context)
{
    const QString refusal = keyRefusal(context);
    if (!refusal.isEmpty())
        return refusal;
    return okReply(ExtensionStorage::value(context.call.extensionId, stringArgument(context, 0)));
}

QString storageKeys(const BridgeContext &context)
{
    return okReply(QJsonArray::fromStringList(ExtensionStorage::keys(context.call.extensionId)));
}

QString storageSet(const BridgeContext &context)
{
    const QString refusal = writeRefusal(context);
    if (!refusal.isEmpty())
        return refusal;
    const auto write = ExtensionStorage::setValue(context.call.extensionId, stringArgument(context, 0),
                                                  context.call.arguments.at(1));
    return write.isWritten ? okReply() : errorReply(write.error);
}

QString storageRemove(const BridgeContext &context)
{
    const QString refusal = writeRefusal(context);
    if (!refusal.isEmpty())
        return refusal;
    ExtensionStorage::removeValue(context.call.extensionId, stringArgument(context, 0));
    return okReply();
}

QString setActionChecked(const BridgeContext &context)
{
    context.tab->extensionItems()->setChecked(context.call.extensionId, stringArgument(context, 0),
                                              context.call.arguments.at(1).toBool());
    return okReply();
}

const TabCommandEntry kTabCommands[] = {
    {"tabs.back", [](Tab &tab) { tab.goBack(); }},
    {"tabs.forward", [](Tab &tab) { tab.goForward(); }},
    {"tabs.reload", [](Tab &tab) { tab.reload(); }},
    {"tabs.close", [](Tab &tab) { tab.closeTab(); }},
    {"tabs.next", [](Tab &tab) { tab.selectNeighborTab(1); }},
    {"tabs.previous", [](Tab &tab) { tab.selectNeighborTab(-1); }},
};

QString runTabCommand(const BridgeContext &context)
{
    for (const TabCommandEntry &entry : kTabCommands) {
        if (context.call.method == QLatin1String(entry.name))
            entry.run(*context.tab);
    }
    return okReply();
}

QString openTab(const BridgeContext &context)
{
    const QUrl url(stringArgument(context, 0), QUrl::StrictMode);
    if (!isWebAddress(url))
        return errorReply(QStringLiteral("Only http and https addresses can be opened"));
    context.tab->openTab(url, context.call.arguments.at(1).toBool());
    return okReply();
}

QString download(const BridgeContext &context)
{
    const QUrl url(stringArgument(context, 0), QUrl::StrictMode);
    if (!isWebAddress(url))
        return errorReply(QStringLiteral("Only http and https addresses can be downloaded"));
    context.tab->downloadUrl(url, stringArgument(context, 1));
    return okReply();
}

QString notify(const BridgeContext &context)
{
    const QString name = ExtensionManager::instance()->displayName(context.call.extensionId);
    Notifier::instance()->notify(QStringLiteral("%1: %2").arg(name, stringArgument(context, 0)),
                                 stringArgument(context, 1), QStringLiteral("preferences-plugin"));
    return okReply();
}

const BridgeMethod kMethods[] = {
    {"storage.get", "", storageGet},
    {"storage.keys", "", storageKeys},
    {"storage.set", "", storageSet},
    {"storage.remove", "", storageRemove},
    {"action.setChecked", "", setActionChecked},
    {"tabs.back", "tabs", runTabCommand},
    {"tabs.forward", "tabs", runTabCommand},
    {"tabs.reload", "tabs", runTabCommand},
    {"tabs.close", "tabs", runTabCommand},
    {"tabs.next", "tabs", runTabCommand},
    {"tabs.previous", "tabs", runTabCommand},
    {"tabs.open", "tabs", openTab},
    {"download", "downloads", download},
    {"notify", "notifications", notify},
};

QString requiredPermission(const QString &method)
{
    if (method.startsWith(QLatin1String("tabs.")))
        return QStringLiteral("tabs");
    for (const BridgeMethod &entry : kMethods) {
        if (method == QLatin1String(entry.name))
            return QString::fromLatin1(entry.permission);
    }
    return QString();
}

QString deniedReply(const QString &permission)
{
    return errorReply(QStringLiteral("Permission denied: this needs the \"%1\" permission")
                          .arg(permission));
}

bool lacksPermission(const BridgeContext &context, const QString &permission)
{
    return !permission.isEmpty()
        && !ExtensionManager::instance()->hasPermission(context.call.extensionId, permission);
}

}

QString handleBridgeCall(const BridgeContext &context)
{
    const QString permission = requiredPermission(context.call.method);
    if (lacksPermission(context, permission))
        return deniedReply(permission);
    for (const BridgeMethod &entry : kMethods) {
        if (context.call.method == QLatin1String(entry.name))
            return entry.handler(context);
    }
    return errorReply(QStringLiteral("Unknown method: %1").arg(context.call.method));
}
