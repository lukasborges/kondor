#include "browser/pagescripts.h"

#include <QFile>
#include <QVariant>
#include <QQuickWebEngineProfile>
#include <QWebEngineScript>

#include <optional>

namespace {
struct ScriptSpec
{
    QString name;
    QString source;
    QWebEngineScript::InjectionPoint injectionPoint;
};

std::optional<QString> readResource(const QString &path)
{
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly))
        return std::nullopt;
    return QString::fromUtf8(file.readAll());
}

QWebEngineScript makeScript(const ScriptSpec &spec)
{
    QWebEngineScript script;
    script.setName(spec.name);
    script.setSourceCode(spec.source);
    script.setInjectionPoint(spec.injectionPoint);
    script.setWorldId(QWebEngineScript::ApplicationWorld);
    script.setRunsOnSubFrames(true);
    return script;
}

bool insertScript(QObject *collection, const QWebEngineScript &script)
{
    if (collection
        && QMetaObject::invokeMethod(collection, "insert", Q_ARG(QWebEngineScript, script)))
        return true;
    qWarning("Cannot install the page script %s", qPrintable(script.name()));
    return false;
}

bool installChannelScript(QObject *collection)
{
    const auto webChannel = readResource(QStringLiteral(":/qtwebchannel/qwebchannel.js"));
    const auto channel = readResource(QStringLiteral(":/scripts/channel.js"));
    if (!webChannel || !channel) {
        qWarning("Web channel script resources not found: autofill and extensions are off");
        return false;
    }
    const QString source = *webChannel + QLatin1Char('\n') + *channel;
    const ScriptSpec spec{QStringLiteral("kondor-channel"), source, QWebEngineScript::DocumentCreation};
    return insertScript(collection, makeScript(spec));
}

void installPasswordsScript(QObject *collection)
{
    const auto usernameField = readResource(QStringLiteral(":/scripts/usernamefield.js"));
    const auto passwords = readResource(QStringLiteral(":/scripts/passwords.js"));
    if (!usernameField || !passwords) {
        qWarning("Password script resource not found: autofill is off");
        return;
    }
    const QString source = *usernameField + QLatin1Char('\n') + *passwords;
    const ScriptSpec spec{QStringLiteral("kondor-passwords"), source, QWebEngineScript::DocumentReady};
    insertScript(collection, makeScript(spec));
}
}

void PageScripts::install(QQuickWebEngineProfile *profile)
{
    QObject *collection = profile->property("userScripts").value<QObject *>();
    if (!installChannelScript(collection))
        return;
    if (!profile->isOffTheRecord())
        installPasswordsScript(collection);
}
