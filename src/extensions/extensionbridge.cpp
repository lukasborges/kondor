#include "extensions/extensionbridge.h"

#include <QJsonDocument>
#include <QJsonObject>

#include "extensions/extensionmanager.h"
#include "core/notifier.h"

namespace {

QString okReply(const QJsonValue &value = QJsonValue(QJsonValue::Null))
{
    return QString::fromUtf8(QJsonDocument(QJsonObject{{QStringLiteral("ok"), true},
                                                       {QStringLiteral("value"), value}})
                                 .toJson(QJsonDocument::Compact));
}

QString errorReply(const QString &message)
{
    return QString::fromUtf8(QJsonDocument(QJsonObject{{QStringLiteral("ok"), false},
                                                       {QStringLiteral("error"), message}})
                                 .toJson(QJsonDocument::Compact));
}

} // namespace

ExtensionPageApi::ExtensionPageApi(ExtensionBridge *bridge)
    : QObject(bridge)
    , m_bridge(bridge)
{
}

QString ExtensionPageApi::request(const QString &extensionId, const QString &token,
                                  const QString &method, const QString &argumentsJson)
{
    return m_bridge->request(extensionId, token, method, argumentsJson);
}

ExtensionBridge::ExtensionBridge(QObject *parent)
    : QObject(parent)
    , m_api(new ExtensionPageApi(this))
{
}

void ExtensionBridge::setTab(Tab *tab)
{
    if (m_tab == tab)
        return;
    m_tab = tab;
    emit tabChanged();
}

QString ExtensionBridge::request(const QString &extensionId, const QString &token,
                                 const QString &method, const QString &argumentsJson)
{
    ExtensionManager *manager = ExtensionManager::instance();
    if (!m_tab)
        return errorReply(QStringLiteral("No tab"));
    // One message for an unknown id and a wrong token: nothing to probe.
    if (!manager->checkToken(extensionId, token))
        return errorReply(QStringLiteral("Invalid extension token"));

    const bool isPrivate = m_tab->isPrivate();
    if (!manager->isActive(extensionId, isPrivate))
        return errorReply(QStringLiteral("The extension is turned off"));

    const QJsonDocument document = QJsonDocument::fromJson(argumentsJson.toUtf8());
    const QJsonArray args = document.isArray() ? document.array() : QJsonArray();

    const auto needs = [&](const QString &permission) {
        return manager->hasPermission(extensionId, permission);
    };
    const auto denied = [](const QString &permission) {
        return errorReply(QStringLiteral("Permission denied: this needs the \"%1\" permission")
                              .arg(permission));
    };
    const auto stringArg = [&args](int i) { return args.at(i).toString(); };

    // Storage: no permission needed; read-only in a private tab.
    if (method == QLatin1String("storage.get")) {
        if (!args.at(0).isString())
            return errorReply(QStringLiteral("The key must be a string"));
        return okReply(manager->storageGet(extensionId, stringArg(0)));
    }
    if (method == QLatin1String("storage.keys"))
        return okReply(QJsonArray::fromStringList(manager->storageKeys(extensionId)));
    if (method == QLatin1String("storage.set") || method == QLatin1String("storage.remove")) {
        if (isPrivate)
            return errorReply(QStringLiteral("Storage is read-only in private windows"));
        if (!args.at(0).isString())
            return errorReply(QStringLiteral("The key must be a string"));
        if (method == QLatin1String("storage.remove")) {
            manager->storageRemove(extensionId, stringArg(0));
            return okReply();
        }
        QString error;
        if (!manager->storageSet(extensionId, stringArg(0), args.at(1), &error))
            return errorReply(error);
        return okReply();
    }

    if (method == QLatin1String("action.setChecked")) {
        m_tab->setExtensionItemChecked(extensionId, stringArg(0), args.at(1).toBool());
        return okReply();
    }

    if (method.startsWith(QLatin1String("tabs."))) {
        if (!needs(QStringLiteral("tabs")))
            return denied(QStringLiteral("tabs"));
        if (method == QLatin1String("tabs.back"))
            m_tab->goBack();
        else if (method == QLatin1String("tabs.forward"))
            m_tab->goForward();
        else if (method == QLatin1String("tabs.reload"))
            m_tab->reload();
        else if (method == QLatin1String("tabs.close"))
            m_tab->closeTab();
        else if (method == QLatin1String("tabs.next"))
            m_tab->selectNeighborTab(1);
        else if (method == QLatin1String("tabs.previous"))
            m_tab->selectNeighborTab(-1);
        else if (method == QLatin1String("tabs.open")) {
            const QUrl url(stringArg(0), QUrl::StrictMode);
            const QString scheme = url.scheme();
            if (!url.isValid() || (scheme != QLatin1String("http") && scheme != QLatin1String("https")))
                return errorReply(QStringLiteral("Only http and https addresses can be opened"));
            m_tab->openTab(url, args.at(1).toBool());
        } else {
            return errorReply(QStringLiteral("Unknown method: %1").arg(method));
        }
        return okReply();
    }

    if (method == QLatin1String("download")) {
        if (!needs(QStringLiteral("downloads")))
            return denied(QStringLiteral("downloads"));
        const QUrl url(stringArg(0), QUrl::StrictMode);
        const QString scheme = url.scheme();
        if (!url.isValid() || (scheme != QLatin1String("http") && scheme != QLatin1String("https")))
            return errorReply(QStringLiteral("Only http and https addresses can be downloaded"));
        m_tab->downloadUrl(url, stringArg(1));
        return okReply();
    }

    if (method == QLatin1String("notify")) {
        if (!needs(QStringLiteral("notifications")))
            return denied(QStringLiteral("notifications"));
        Notifier::instance()->notify(
            QStringLiteral("%1: %2").arg(manager->displayName(extensionId), stringArg(0)),
            stringArg(1), QStringLiteral("preferences-plugin"));
        return okReply();
    }

    return errorReply(QStringLiteral("Unknown method: %1").arg(method));
}
