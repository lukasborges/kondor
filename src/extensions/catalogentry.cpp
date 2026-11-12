#include "extensions/catalogentry.h"

#include <QCoreApplication>
#include <QJsonArray>
#include <QJsonDocument>
#include <QVersionNumber>

#include "extensions/extensionpackage.h"

namespace {

QStringList stringList(const QJsonValue &value)
{
    QStringList list;
    const QJsonArray array = value.toArray();
    for (const QJsonValue &item : array) {
        if (item.isString())
            list.append(item.toString());
    }
    return list;
}

CatalogEntry identityOf(const QJsonObject &object)
{
    CatalogEntry entry;
    entry.json = object;
    entry.id = object.value(QLatin1String("id")).toString();
    entry.version = object.value(QLatin1String("version")).toString();
    entry.matches = stringList(object.value(QLatin1String("matches")));
    entry.permissions = stringList(object.value(QLatin1String("permissions")));
    entry.sha256 = object.value(QLatin1String("sha256")).toString().toLower();
    entry.size = qint64(object.value(QLatin1String("size")).toDouble());
    return entry;
}

QString iconSourceOf(const QString &icon, const QUrl &catalogUrl)
{
    if (icon.isEmpty())
        return QStringLiteral("preferences-plugin");
    if (icon.contains(QLatin1Char('/')) || icon.contains(QLatin1Char('.')))
        return catalogUrl.resolved(QUrl(icon)).toString();
    return icon;
}

bool hasSupportedFormat(const QJsonObject &root)
{
    return root.value(QLatin1String("version")).toInt() == 1
        && root.value(QLatin1String("extensions")).isArray();
}

QList<CatalogEntry> entriesOf(const QJsonArray &array, const QUrl &catalogUrl)
{
    QList<CatalogEntry> entries;
    for (const QJsonValue &value : array) {
        if (const auto entry = parseCatalogEntry(value.toObject(), catalogUrl))
            entries.append(*entry);
    }
    return entries;
}

}

std::optional<CatalogEntry> parseCatalogEntry(const QJsonObject &object, const QUrl &catalogUrl)
{
    const QString package = object.value(QLatin1String("package")).toString();
    CatalogEntry entry = identityOf(object);
    if (!ExtensionPackage::isValidId(entry.id) || entry.version.isEmpty() || package.isEmpty())
        return std::nullopt;
    entry.package = catalogUrl.resolved(QUrl(package));
    entry.iconSource = iconSourceOf(object.value(QLatin1String("icon")).toString(), catalogUrl);
    return entry;
}

std::optional<QList<CatalogEntry>> parseCatalog(const QByteArray &json, const QUrl &catalogUrl,
                                                QString &error)
{
    QJsonParseError parseError;
    const QJsonDocument document = QJsonDocument::fromJson(json, &parseError);
    const QJsonObject root = document.object();
    if (parseError.error != QJsonParseError::NoError || !document.isObject())
        error = QCoreApplication::translate("ExtensionCatalog", "The catalog is not valid JSON");
    else if (!hasSupportedFormat(root))
        error = QCoreApplication::translate("ExtensionCatalog", "The catalog has an unsupported format");
    else
        return entriesOf(root.value(QLatin1String("extensions")).toArray(), catalogUrl);
    return std::nullopt;
}

bool isNewerVersion(const QString &candidate, const QString &installed)
{
    return QVersionNumber::fromString(candidate) > QVersionNumber::fromString(installed);
}
