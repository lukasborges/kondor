#pragma once

#include <QString>
#include <QStringList>
#include <QVariantMap>
#include <QWebEngineScript>

#include "extensions/package/extensionpackage.h"

struct ContentScriptContext {
    const ExtensionPackage *package = nullptr;
    int index = 0;
    QString token;
    QString locale;
    bool isPrivate = false;
    QVariantMap settings;
    QStringList disabledSites;
};

QString contentScriptSource(const ContentScriptContext &context);
QWebEngineScript contentScript(const ContentScriptContext &context);
