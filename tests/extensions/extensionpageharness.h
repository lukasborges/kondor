#pragma once

#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickItem>
#include <QQuickWebEngineProfile>
#include <QQuickWindow>

#include "extensions/extensionbridge.h"
#include "extensionsharness.h"

constexpr const char *pageViewQml =
    "import QtQuick\nimport QtWebEngine\nimport QtWebChannel\n"
    "WebEngineView {\n"
    "    id: view\n"
    "    property var result\n"
    "    property bool done: false\n"
    "    property alias pageChannel: channel\n"
    "    property bool loaded: false\n"
    "    onLoadingChanged: function(info) {\n"
    "        if (info.status === WebEngineLoadingInfo.LoadSucceededStatus) loaded = true\n"
    "    }\n"
    "    function load(address) { loaded = false; url = address }\n"
    "    width: 400; height: 300\n"
    "    webChannel: channel\n"
    "    webChannelWorld: WebEngineScript.ApplicationWorld\n"
    "    WebChannel { id: channel }\n"
    "    function run(code) {\n"
    "        done = false; result = undefined\n"
    "        runJavaScript(code, WebEngineScript.MainWorld, function(r) { result = r; done = true })\n"
    "    }\n"
    "}\n";

struct Page {
    QQuickItem *view = nullptr;
    Tab *tab = nullptr;
    ExtensionBridge *bridge = nullptr;
};

class PageHost
{
public:
    PageHost()
    {
        m_window.resize(400, 300);
        m_window.show();
    }

    Page open(QQuickWebEngineProfile *profile, const QUrl &url)
    {
        Page page;
        page.view = createView(profile);
        if (!page.view)
            return page;
        page.view->setParentItem(m_window.contentItem());
        page.tab = new Tab(profile, page.view);
        page.bridge = new ExtensionBridge(page.view);
        page.bridge->setTab(page.tab);
        registerPageApi(page);
        QMetaObject::invokeMethod(page.view, "load", Q_ARG(QVariant, url));
        return page;
    }

private:
    QQuickItem *createView(QQuickWebEngineProfile *profile)
    {
        QQmlComponent component(&m_engine);
        component.setData(pageViewQml, QUrl());
        auto *view = qobject_cast<QQuickItem *>(component.createWithInitialProperties(
            {{QStringLiteral("profile"), QVariant::fromValue(profile)}}));
        if (!view)
            qWarning() << component.errors();
        return view;
    }

    static void registerPageApi(const Page &page)
    {
        QObject *channel = page.view->property("pageChannel").value<QObject *>();
        QMetaObject::invokeMethod(channel, "registerObject", Q_ARG(QString, QStringLiteral("kondorExtensions")),
                                  Q_ARG(QObject *, page.bridge->pageApi()));
    }

    QQmlEngine m_engine;
    QQuickWindow m_window;
};

inline void loadUrl(const Page &page, const QUrl &url)
{
    QMetaObject::invokeMethod(page.view, "load", Q_ARG(QVariant, url));
}

inline QVariant evaluate(const Page &page, const QString &code)
{
    QMetaObject::invokeMethod(page.view, "run", Q_ARG(QVariant, code));
    (void)QTest::qWaitFor([&]() { return page.view->property("done").toBool(); }, 5000);
    return page.view->property("result");
}

inline bool waitLoaded(const Page &page)
{
    return QTest::qWaitFor([&]() { return page.view->property("loaded").toBool(); }, 30000);
}

inline QVariant attribute(const Page &page, const QString &name)
{
    return evaluate(page, QStringLiteral("document.readyState === 'complete' ? "
                                         "document.documentElement.getAttribute('%1') : 'loading'").arg(name));
}

inline void runInApplicationWorld(const Page &page, const QString &script)
{
    QMetaObject::invokeMethod(page.view, "runJavaScript", Q_ARG(QString, script),
                              Q_ARG(uint, uint(QWebEngineScript::ApplicationWorld)));
}
