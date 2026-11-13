#include "extensions/bridge/extensioncall.h"

#include <QJsonDocument>
#include <QJsonObject>

namespace {

QString compact(const QJsonObject &object)
{
    return QString::fromUtf8(QJsonDocument(object).toJson(QJsonDocument::Compact));
}

}

ExtensionCall parseExtensionCall(const QString &requestJson)
{
    const QJsonObject request = QJsonDocument::fromJson(requestJson.toUtf8()).object();
    ExtensionCall call;
    call.extensionId = request.value(QLatin1String("id")).toString();
    call.token = request.value(QLatin1String("token")).toString();
    call.method = request.value(QLatin1String("method")).toString();
    call.arguments = request.value(QLatin1String("arguments")).toArray();
    return call;
}

QString okReply(const QJsonValue &value)
{
    return compact(QJsonObject{{QStringLiteral("ok"), true}, {QStringLiteral("value"), value}});
}

QString errorReply(const QString &message)
{
    return compact(QJsonObject{{QStringLiteral("ok"), false}, {QStringLiteral("error"), message}});
}
