#include "extensions/contentscriptreader.h"

#include "extensions/manifestsections.h"
#include "extensions/packagepath.h"
#include "extensions/stringlistfield.h"

namespace {

const QStringList &knownRunAtValues()
{
    static const QStringList values{QStringLiteral("document-start"),
                                    QStringLiteral("document-end"),
                                    QStringLiteral("document-idle")};
    return values;
}

}

ContentScriptReader::ContentScriptReader(const QString &directory, const QString &where)
    : m_directory(directory)
    , m_where(where)
{
}

std::optional<ExtensionContentScript> ContentScriptReader::read(const QJsonObject &object)
{
    ExtensionContentScript script;
    if (!readLists(object, script) || !checkLists(script) || !readRunAt(object, script))
        return std::nullopt;
    script.allFrames = object.value(QLatin1String("allFrames")).toBool(false);
    return script;
}

bool ContentScriptReader::readLists(const QJsonObject &object, ExtensionContentScript &script)
{
    return readList(object, QStringLiteral("matches"), script.matches)
        && readList(object, QStringLiteral("exclude"), script.exclude)
        && readList(object, QStringLiteral("js"), script.js)
        && readList(object, QStringLiteral("css"), script.css);
}

bool ContentScriptReader::readList(const QJsonObject &object, const QString &key,
                                   QStringList &target)
{
    const bool isRequired = key == QLatin1String("matches");
    const auto list = readStringList(object, {key, m_where, isRequired}, m_error);
    if (list)
        target = *list;
    return list.has_value();
}

bool ContentScriptReader::checkLists(const ExtensionContentScript &script)
{
    if (script.matches.isEmpty())
        return fail(QStringLiteral("%1.matches: must not be empty").arg(m_where));
    if (script.js.isEmpty() && script.css.isEmpty())
        return fail(QStringLiteral("%1: needs at least one js or css file").arg(m_where));
    return checkFiles(script.js, ".js") && checkFiles(script.css, ".css");
}

bool ContentScriptReader::checkFiles(const QStringList &files, const char *kind)
{
    for (const QString &file : files) {
        m_error = packageFileError(m_directory, file, m_where + QLatin1String(kind));
        if (!m_error.isEmpty())
            return false;
    }
    return true;
}

bool ContentScriptReader::readRunAt(const QJsonObject &object, ExtensionContentScript &script)
{
    const QJsonValue runAt = object.value(QLatin1String("runAt"));
    if (runAt.isUndefined())
        return true;
    if (!knownRunAtValues().contains(runAt.toString()))
        return fail(QStringLiteral("%1.runAt: must be document-start, document-end or "
                                   "document-idle").arg(m_where));
    script.runAt = runAt.toString();
    return true;
}

bool ContentScriptReader::fail(const QString &message)
{
    m_error = manifestError(message);
    return false;
}
