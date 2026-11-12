#pragma once

#include <QJsonValue>
#include <QString>

QString manifestError(const QString &message);
QString settingsError(const QJsonValue &settings);
QString actionError(const QJsonValue &action);
