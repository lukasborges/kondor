#pragma once

#include <QJsonValue>
#include <QString>
#include <QStringList>

namespace ExtensionStorage {

constexpr qint64 kStorageQuota = 1024 * 1024;

struct StorageWrite {
    bool isWritten = false;
    QString error;
};

QJsonValue value(const QString &id, const QString &key);
StorageWrite setValue(const QString &id, const QString &key, const QJsonValue &value);
void removeValue(const QString &id, const QString &key);
QStringList keys(const QString &id);
void removeExtension(const QString &id);

}
