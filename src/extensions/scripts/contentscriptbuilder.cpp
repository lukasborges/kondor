#include "extensions/contentscriptbuilder.h"

#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLocale>

namespace {

struct InjectionPoint {
    const char *runAt;
    QWebEngineScript::InjectionPoint point;
};

const InjectionPoint kInjectionPoints[] = {
    {"document-start", QWebEngineScript::DocumentCreation},
    {"document-end", QWebEngineScript::DocumentReady},
};

const char kSiteCheck[] =
    "\nif (__cfg.disabledSites.indexOf(location.origin) !== -1)\n    return;\n"
    "const kondor = __kondorCreateRuntime(__cfg);\n";

const char kStyleInjector[] =
    "(function (styles) {\n"
    "    if (styles.length === 0) return;\n"
    "    function add() {\n"
    "        styles.forEach(function (text) {\n"
    "            const style = document.createElement(\"style\");\n"
    "            style.textContent = text;\n"
    "            document.documentElement.appendChild(style);\n"
    "        });\n"
    "    }\n"
    "    if (document.documentElement) { add(); return; }\n"
    "    new MutationObserver(function (records, observer) {\n"
    "        if (document.documentElement) { observer.disconnect(); add(); }\n"
    "    }).observe(document, { childList: true });\n"
    "})(__cfg.css);\n";

QString runtimeSource()
{
    static const QString source = []() {
        QFile file(QStringLiteral(":/scripts/extensionruntime.js"));
        if (file.open(QIODevice::ReadOnly))
            return QString::fromUtf8(file.readAll());
        qWarning("Extension runtime script not found: extensions are off");
        return QString();
    }();
    return source;
}

QString compact(const QJsonObject &object)
{
    return QString::fromUtf8(QJsonDocument(object).toJson(QJsonDocument::Compact));
}

QString fileText(const ExtensionPackage &package, const QString &file)
{
    return QString::fromUtf8(package.readFile(file));
}

QString metadataBlock(const ExtensionContentScript &content)
{
    QString block = QStringLiteral("// ==UserScript==\n");
    for (const QString &match : content.matches)
        block += QStringLiteral("// @match %1\n").arg(match);
    for (const QString &exclude : content.exclude)
        block += QStringLiteral("// @exclude %1\n").arg(exclude);
    block += QStringLiteral("// @run-at %1\n").arg(content.runAt);
    return block + QStringLiteral("// ==/UserScript==\n");
}

QJsonArray styleTexts(const ExtensionPackage &package, const ExtensionContentScript &content)
{
    QJsonArray styles;
    for (const QString &file : content.css)
        styles.append(fileText(package, file));
    return styles;
}

QJsonObject packageFields(const ExtensionPackage &package, const ExtensionContentScript &content)
{
    return QJsonObject{
        {QStringLiteral("id"), package.id()},
        {QStringLiteral("version"), package.version()},
        {QStringLiteral("css"), styleTexts(package, content)},
    };
}

QString localeOf(const ContentScriptContext &context)
{
    return context.locale.isEmpty() ? QLocale::system().name() : context.locale;
}

QString configurationObject(const ContentScriptContext &context, const ExtensionContentScript &content)
{
    QJsonObject object = packageFields(*context.package, content);
    object.insert(QStringLiteral("token"), context.token);
    object.insert(QStringLiteral("locale"), localeOf(context));
    object.insert(QStringLiteral("isPrivate"), context.isPrivate);
    object.insert(QStringLiteral("settings"), QJsonObject::fromVariantMap(context.settings));
    object.insert(QStringLiteral("disabledSites"), QJsonArray::fromStringList(context.disabledSites));
    return compact(object);
}

QString javaScriptFiles(const ExtensionPackage &package, const ExtensionContentScript &content)
{
    if (content.js.isEmpty())
        return QString();
    QString source = QStringLiteral("(function (kondor) {\n");
    for (const QString &file : content.js)
        source += fileText(package, file) + QStringLiteral("\n;\n");
    return source + QStringLiteral("})(kondor);\n");
}

QString scriptBody(const ContentScriptContext &context, const ExtensionContentScript &content)
{
    return QStringLiteral("(function () {\nconst __cfg = ") + configurationObject(context, content)
        + QStringLiteral(";\n") + runtimeSource() + QLatin1String(kSiteCheck)
        + QLatin1String(kStyleInjector) + javaScriptFiles(*context.package, content)
        + QStringLiteral("})();\n");
}

QWebEngineScript::InjectionPoint injectionPointFor(const QString &runAt)
{
    for (const InjectionPoint &entry : kInjectionPoints) {
        if (runAt == QLatin1String(entry.runAt))
            return entry.point;
    }
    return QWebEngineScript::Deferred;
}

const ExtensionContentScript &contentOf(const ContentScriptContext &context)
{
    return context.package->contentScripts().at(context.index);
}

}

QString contentScriptSource(const ContentScriptContext &context)
{
    const ExtensionContentScript &content = contentOf(context);
    return metadataBlock(content) + scriptBody(context, content);
}

QWebEngineScript contentScript(const ContentScriptContext &context)
{
    QWebEngineScript script;
    script.setName(QStringLiteral("kondor-ext:%1:%2").arg(context.package->id()).arg(context.index));
    script.setSourceCode(contentScriptSource(context));
    script.setWorldId(QWebEngineScript::ApplicationWorld);
    script.setRunsOnSubFrames(contentOf(context).allFrames);
    script.setInjectionPoint(injectionPointFor(contentOf(context).runAt));
    return script;
}
