#include "app/instance/singleinstancemessage.h"

#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>

namespace {
QJsonArray encodeUrls(const QList<QUrl> &urls)
{
    QJsonArray array;
    for (const QUrl &url : urls)
        array.append(QString::fromUtf8(url.toEncoded()));
    return array;
}

QList<QUrl> decodeUrls(const QJsonArray &array)
{
    QList<QUrl> urls;
    for (const QJsonValue &value : array) {
        const QUrl url = QUrl::fromEncoded(value.toString().toUtf8());
        if (url.isValid() && !url.isEmpty())
            urls.append(url);
    }
    return urls;
}

SingleInstanceMessage fromObject(const QJsonObject &object)
{
    SingleInstanceMessage message;
    message.urls = decodeUrls(object.value(QStringLiteral("urls")).toArray());
    message.privateMode = object.value(QStringLiteral("private")).toBool();
    message.newWindow = object.value(QStringLiteral("newWindow")).toBool();
    message.activationToken =
        object.value(QStringLiteral("activationToken")).toString().toUtf8();
    return message;
}
}

QByteArray SingleInstanceMessage::toJsonLine() const
{
    QJsonObject object;
    object.insert(QStringLiteral("urls"), encodeUrls(urls));
    object.insert(QStringLiteral("private"), privateMode);
    object.insert(QStringLiteral("newWindow"), newWindow);
    object.insert(QStringLiteral("activationToken"), QString::fromUtf8(activationToken));
    return QJsonDocument(object).toJson(QJsonDocument::Compact) + '\n';
}

SingleInstanceMessage SingleInstanceMessage::fromJsonLine(const QByteArray &line)
{
    const QJsonDocument document = QJsonDocument::fromJson(line.trimmed());
    if (!document.isObject())
        return {};
    return fromObject(document.object());
}
