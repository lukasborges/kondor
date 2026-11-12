#pragma once

#include <QJsonObject>
#include <QString>
#include <QVariantList>
#include <QVariantMap>

namespace LocalizedManifest {

QString localized(const QJsonObject &object, const QString &key, const QString &locale);
QVariantList settingsSchema(const QJsonObject &manifest, const QString &locale);
QVariantMap settingDefaults(const QJsonObject &manifest);
QVariantList actionItems(const QJsonObject &manifest, const QString &locale);

}
