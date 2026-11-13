#include "core/settings/searchengines.h"

#include <QHash>

namespace SearchEngines {

namespace {

struct Engine {
    QString name;
    QString urlTemplate;
};

const Engine &fallbackEngine()
{
    static const Engine engine{QStringLiteral("DuckDuckGo"),
                               QStringLiteral("https://duckduckgo.com/?q=%1")};
    return engine;
}

const QHash<QString, Engine> &builtInEngines()
{
    static const QHash<QString, Engine> engines = {
        {QStringLiteral("duckduckgo"), fallbackEngine()},
        {QStringLiteral("google"),
         {QStringLiteral("Google"), QStringLiteral("https://www.google.com/search?q=%1")}},
        {QStringLiteral("startpage"),
         {QStringLiteral("Startpage"), QStringLiteral("https://www.startpage.com/do/search?q=%1")}},
        {QStringLiteral("brave"),
         {QStringLiteral("Brave Search"), QStringLiteral("https://search.brave.com/search?q=%1")}},
    };
    return engines;
}

bool isUsableCustomEngine(const QString &engineId, const QString &customUrl)
{
    return engineId == QLatin1String("custom") && customUrl.contains(QLatin1String("%1"));
}

Engine engineFor(const QString &engineId)
{
    return builtInEngines().value(engineId, fallbackEngine());
}

}

QString urlTemplate(const QString &engineId, const QString &customUrl)
{
    if (isUsableCustomEngine(engineId, customUrl))
        return customUrl;
    return engineFor(engineId).urlTemplate;
}

QString displayName(const QString &engineId, const QString &customUrl)
{
    if (isUsableCustomEngine(engineId, customUrl))
        return QString();
    return engineFor(engineId).name;
}

}
