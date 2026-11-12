#pragma once

#include <QJsonObject>
#include <QList>
#include <QString>
#include <QStringList>
#include <QUrl>

#include <optional>

struct CatalogEntry {
    QString id;
    QJsonObject json;
    QString version;
    QStringList matches;
    QStringList permissions;
    QUrl package;
    QString sha256;
    qint64 size = 0;
    QString iconSource;
};

std::optional<CatalogEntry> parseCatalogEntry(const QJsonObject &object, const QUrl &catalogUrl);
std::optional<QList<CatalogEntry>> parseCatalog(const QByteArray &json, const QUrl &catalogUrl,
                                                QString &error);
bool isNewerVersion(const QString &candidate, const QString &installed);
