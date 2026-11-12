#pragma once

#include <QJsonObject>
#include <QString>

#include <optional>

#include "extensions/extensionpackage.h"

class ContentScriptReader
{
public:
    ContentScriptReader(const QString &directory, const QString &where);

    std::optional<ExtensionContentScript> read(const QJsonObject &object);
    QString error() const { return m_error; }

private:
    bool readLists(const QJsonObject &object, ExtensionContentScript &script);
    bool readList(const QJsonObject &object, const QString &key, QStringList &target);
    bool checkLists(const ExtensionContentScript &script);
    bool checkFiles(const QStringList &files, const char *kind);
    bool readRunAt(const QJsonObject &object, ExtensionContentScript &script);
    bool fail(const QString &message);

    QString m_directory;
    QString m_where;
    QString m_error;
};
