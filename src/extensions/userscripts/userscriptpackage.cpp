#include "extensions/userscripts/userscriptpackage.h"

#include <QCoreApplication>
#include <QCryptographicHash>
#include <QDir>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QTemporaryFile>

#include <KZip>

#include "extensions/userscripts/userscriptversion.h"

namespace {

QStringList scriptFiles(const UserScriptSource &source)
{
    QStringList files{QStringLiteral("gm.js")};
    for (qsizetype i = 1; i <= source.requiredScripts.size(); ++i)
        files.append(QStringLiteral("require-%1.js").arg(i));
    files.append(QStringLiteral("script.js"));
    return files;
}

QJsonObject contentScriptOf(const UserScriptSource &source)
{
    const UserScriptMetadata &metadata = source.metadata;
    return QJsonObject{
        {QStringLiteral("matches"), QJsonArray::fromStringList(metadata.matches)},
        {QStringLiteral("include"), QJsonArray::fromStringList(metadata.includes)},
        {QStringLiteral("exclude"), QJsonArray::fromStringList(metadata.excludes)},
        {QStringLiteral("js"), QJsonArray::fromStringList(scriptFiles(source))},
        {QStringLiteral("runAt"), metadata.runAt},
        {QStringLiteral("allFrames"), metadata.allFrames},
    };
}

QJsonObject userScriptSection(const UserScriptSource &source)
{
    const UserScriptMetadata &metadata = source.metadata;
    return QJsonObject{
        {QStringLiteral("version"), metadata.version},
        {QStringLiteral("namespace"), metadata.namespaceName},
        {QStringLiteral("installURL"), source.installUrl.toString()},
        {QStringLiteral("updateURL"), metadata.updateUrl},
        {QStringLiteral("downloadURL"), metadata.downloadUrl},
        {QStringLiteral("unsupported"), QJsonArray::fromStringList(metadata.unsupportedFeatures())},
    };
}

void insertIfPresent(QJsonObject &manifest, const char *key, const QString &value)
{
    if (!value.isEmpty())
        manifest.insert(QLatin1String(key), value);
}

void insertOptionalFields(QJsonObject &manifest, const UserScriptMetadata &metadata)
{
    insertIfPresent(manifest, "description", metadata.description);
    insertIfPresent(manifest, "author", metadata.author);
    insertIfPresent(manifest, "homepage", metadata.homepage);
    insertIfPresent(manifest, "license", metadata.license);
}

QJsonArray permissionsOf(const UserScriptMetadata &metadata)
{
    if (metadata.wantsNotifications())
        return QJsonArray{QStringLiteral("notifications")};
    return QJsonArray();
}

QJsonObject identityOf(const UserScriptMetadata &metadata)
{
    return QJsonObject{
        {QStringLiteral("kondor"), 1},
        {QStringLiteral("id"), userScriptId(metadata)},
        {QStringLiteral("name"), metadata.name},
        {QStringLiteral("version"), normalizedUserScriptVersion(metadata.version)},
        {QStringLiteral("icon"), QStringLiteral("text-x-javascript")},
        {QStringLiteral("permissions"), permissionsOf(metadata)},
    };
}

QString gmDeclaration(const UserScriptMetadata &metadata)
{
    const QJsonObject script{
        {QStringLiteral("name"), metadata.name},
        {QStringLiteral("namespace"), metadata.namespaceName},
        {QStringLiteral("version"), metadata.version},
        {QStringLiteral("description"), metadata.description},
        {QStringLiteral("kondorVersion"), QCoreApplication::applicationVersion()},
    };
    return QStringLiteral("const __userScript = ")
        + QString::fromUtf8(QJsonDocument(script).toJson(QJsonDocument::Compact))
        + QStringLiteral(";\n");
}

QString gmSource(const UserScriptMetadata &metadata)
{
    QFile file(QStringLiteral(":/scripts/usergm.js"));
    if (!file.open(QIODevice::ReadOnly))
        return QString();
    return gmDeclaration(metadata) + QString::fromUtf8(file.readAll());
}

bool writeEntries(KZip &zip, const UserScriptSource &source)
{
    bool isWritten = zip.writeFile(QStringLiteral("manifest.json"),
                                   QJsonDocument(userScriptManifest(source)).toJson());
    isWritten = zip.writeFile(QStringLiteral("gm.js"), gmSource(source.metadata).toUtf8()) && isWritten;
    for (qsizetype i = 0; i < source.requiredScripts.size(); ++i)
        isWritten = zip.writeFile(QStringLiteral("require-%1.js").arg(i + 1),
                                  source.requiredScripts.at(i)) && isWritten;
    return zip.writeFile(QStringLiteral("script.js"), source.script) && isWritten;
}

bool writeZip(const QString &path, const UserScriptSource &source)
{
    KZip zip(path);
    if (!zip.open(QIODevice::WriteOnly))
        return false;
    const bool isWritten = writeEntries(zip, source);
    return zip.close() && isWritten;
}

}

QString userScriptId(const UserScriptMetadata &metadata)
{
    const QByteArray identity = (metadata.namespaceName + QLatin1Char('\n') + metadata.name).toUtf8();
    const QByteArray hash = QCryptographicHash::hash(identity, QCryptographicHash::Sha256).toHex();
    return QStringLiteral("user-") + QString::fromLatin1(hash.left(16));
}

QJsonObject userScriptManifest(const UserScriptSource &source)
{
    QJsonObject manifest = identityOf(source.metadata);
    manifest.insert(QStringLiteral("contentScripts"), QJsonArray{contentScriptOf(source)});
    manifest.insert(QStringLiteral("userScript"), userScriptSection(source));
    insertOptionalFields(manifest, source.metadata);
    return manifest;
}

QUrl userScriptDownloadUrl(const QJsonObject &userScript)
{
    const QString download = userScript.value(QLatin1String("downloadURL")).toString();
    return QUrl(download.isEmpty() ? userScript.value(QLatin1String("installURL")).toString() : download);
}

std::optional<QString> writeUserScriptPackage(const UserScriptSource &source, QString &error)
{
    QTemporaryFile file(QDir::tempPath() + QStringLiteral("/kondor-userscript-XXXXXX.kondorext"));
    file.setAutoRemove(false);
    if (file.open()) {
        file.close();
        if (writeZip(file.fileName(), source))
            return file.fileName();
        QFile::remove(file.fileName());
    }
    error = QCoreApplication::translate("UserScript", "Cannot create the package");
    return std::nullopt;
}
