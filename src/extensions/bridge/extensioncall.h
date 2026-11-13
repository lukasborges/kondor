#pragma once

#include <QJsonArray>
#include <QJsonValue>
#include <QString>

struct ExtensionCall {
    QString extensionId;
    QString token;
    QString method;
    QJsonArray arguments;
};

ExtensionCall parseExtensionCall(const QString &requestJson);
QString okReply(const QJsonValue &value = QJsonValue(QJsonValue::Null));
QString errorReply(const QString &message);
