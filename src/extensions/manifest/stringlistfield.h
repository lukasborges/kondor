#pragma once

#include <QJsonObject>
#include <QString>
#include <QStringList>

#include <optional>

struct StringListField {
    QString key;
    QString path;
    bool isRequired = false;
};

std::optional<QStringList> readStringList(const QJsonObject &object, const StringListField &field,
                                          QString &error);
