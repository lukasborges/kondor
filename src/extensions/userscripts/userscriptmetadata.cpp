#include "extensions/userscripts/userscriptmetadata.h"

#include <QCoreApplication>
#include <QRegularExpression>

namespace {

struct StringField {
    const char *key;
    QString UserScriptMetadata::*member;
};

struct ListField {
    const char *key;
    QStringList UserScriptMetadata::*member;
};

const StringField kStringFields[] = {
    {"name", &UserScriptMetadata::name},
    {"namespace", &UserScriptMetadata::namespaceName},
    {"version", &UserScriptMetadata::version},
    {"description", &UserScriptMetadata::description},
    {"author", &UserScriptMetadata::author},
    {"license", &UserScriptMetadata::license},
    {"updateURL", &UserScriptMetadata::updateUrl},
    {"downloadURL", &UserScriptMetadata::downloadUrl},
};

const ListField kListFields[] = {
    {"match", &UserScriptMetadata::matches},
    {"include", &UserScriptMetadata::includes},
    {"exclude", &UserScriptMetadata::excludes},
    {"exclude-match", &UserScriptMetadata::excludes},
    {"grant", &UserScriptMetadata::grants},
    {"require", &UserScriptMetadata::requiredUrls},
};

const QStringList &supportedGrants()
{
    static const QStringList grants{
        QStringLiteral("none"), QStringLiteral("GM.info"), QStringLiteral("GM_info"),
        QStringLiteral("GM.getValue"), QStringLiteral("GM.setValue"),
        QStringLiteral("GM.deleteValue"), QStringLiteral("GM.listValues"),
        QStringLiteral("GM.addStyle"), QStringLiteral("GM_addStyle"),
        QStringLiteral("GM.notification"), QStringLiteral("GM_notification")};
    return grants;
}

QString translated(const char *text)
{
    return QCoreApplication::translate("UserScript", text);
}

QStringList blockLines(const QString &source)
{
    static const QRegularExpression start(QStringLiteral("^\\s*//\\s*==UserScript==\\s*$"));
    static const QRegularExpression end(QStringLiteral("^\\s*//\\s*==/UserScript==\\s*$"));
    const QStringList lines = source.split(QLatin1Char('\n'));
    const qsizetype first = lines.indexOf(start);
    if (first < 0)
        return {};
    const qsizetype last = lines.indexOf(end, first);
    return last < 0 ? QStringList() : lines.mid(first + 1, last - first - 1);
}

std::optional<QPair<QString, QString>> keyAndValue(const QString &line)
{
    static const QRegularExpression pattern(QStringLiteral("^\\s*//\\s*@([\\w:.-]+)\\s*(.*?)\\s*$"));
    const QRegularExpressionMatch match = pattern.match(line);
    if (!match.hasMatch())
        return std::nullopt;
    return qMakePair(match.captured(1), match.captured(2));
}

QString mappedRunAt(const QString &value)
{
    if (value == QLatin1String("document-start"))
        return value;
    const bool isEnd = value == QLatin1String("document-end") || value == QLatin1String("document-body");
    return isEnd ? QStringLiteral("document-end") : QStringLiteral("document-idle");
}

bool isHomepageKey(const QString &key)
{
    return key == QLatin1String("homepageURL") || key == QLatin1String("homepage")
        || key == QLatin1String("website");
}

bool applyStringField(UserScriptMetadata &metadata, const QString &key, const QString &value)
{
    for (const StringField &field : kStringFields) {
        if (key != QLatin1String(field.key))
            continue;
        if ((metadata.*field.member).isEmpty())
            metadata.*field.member = value;
        return true;
    }
    return false;
}

bool applyListField(UserScriptMetadata &metadata, const QString &key, const QString &value)
{
    for (const ListField &field : kListFields) {
        if (key != QLatin1String(field.key))
            continue;
        (metadata.*field.member).append(value);
        return true;
    }
    return false;
}

void applySpecialField(UserScriptMetadata &metadata, const QString &key, const QString &value)
{
    if (isHomepageKey(key) && metadata.homepage.isEmpty())
        metadata.homepage = value;
    else if (key == QLatin1String("run-at"))
        metadata.runAt = mappedRunAt(value);
    else if (key == QLatin1String("noframes"))
        metadata.allFrames = false;
    else if (key == QLatin1String("resource"))
        metadata.usesResource = true;
}

void applyField(UserScriptMetadata &metadata, const QString &key, const QString &value)
{
    if (!applyStringField(metadata, key, value) && !applyListField(metadata, key, value))
        applySpecialField(metadata, key, value);
}

QString problemOf(const QStringList &lines, const UserScriptMetadata &metadata)
{
    if (lines.isEmpty())
        return translated(QT_TRANSLATE_NOOP("UserScript", "The script has no metadata block"));
    if (metadata.name.isEmpty())
        return translated(QT_TRANSLATE_NOOP("UserScript", "The script has no @name"));
    if (metadata.matches.isEmpty() && metadata.includes.isEmpty())
        return translated(QT_TRANSLATE_NOOP("UserScript", "The script has neither @match nor @include"));
    return QString();
}

UserScriptMetadata metadataFrom(const QStringList &lines)
{
    UserScriptMetadata metadata;
    for (const QString &line : lines) {
        const auto pair = keyAndValue(line);
        if (pair)
            applyField(metadata, pair->first, pair->second);
    }
    return metadata;
}

}

QStringList UserScriptMetadata::unsupportedFeatures() const
{
    QStringList unsupported;
    for (const QString &grant : grants) {
        if (!supportedGrants().contains(grant) && !unsupported.contains(grant))
            unsupported.append(grant);
    }
    if (usesResource)
        unsupported.append(QStringLiteral("@resource"));
    return unsupported;
}

bool UserScriptMetadata::wantsNotifications() const
{
    return grants.contains(QLatin1String("GM.notification"))
        || grants.contains(QLatin1String("GM_notification"));
}

std::optional<UserScriptMetadata> parseUserScriptMetadata(const QString &source, QString &error)
{
    const QStringList lines = blockLines(source);
    const UserScriptMetadata metadata = metadataFrom(lines);
    error = problemOf(lines, metadata);
    if (!error.isEmpty())
        return std::nullopt;
    return metadata;
}
