#pragma once

#include <QFile>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQmlExpression>
#include <QQuickImageProvider>
#include <QQuickWindow>
#include <QRegularExpression>
#include <QTest>

#include "bookmarks/bookmarkmanager.h"
#include "browser/favicons/faviconstore.h"
#include "browser/profile/profilemanager.h"
#include "browser/tabs/tab.h"
#include "browser/tabs/tabmodel.h"
#include "../common/qmltesthelpers.h"
#include "core/database/database.h"
#include "core/settings/settings.h"
#include "history/historymanager.h"
#include "mainmenustub.h"

inline QStringList &collectedWarnings()
{
    static QStringList warnings;
    return warnings;
}

inline QtMessageHandler &previousMessageHandler()
{
    static QtMessageHandler handler = nullptr;
    return handler;
}

inline void collectWarnings(QtMsgType type, const QMessageLogContext &context,
                            const QString &message)
{
    collectedWarnings() << message;
    previousMessageHandler()(type, context, message);
}

class EmptyImageProvider : public QQuickImageProvider
{
public:
    EmptyImageProvider() : QQuickImageProvider(QQuickImageProvider::Image) {}
    QImage requestImage(const QString &, QSize *size, const QSize &) override
    {
        QImage image(1, 1, QImage::Format_ARGB32);
        image.fill(Qt::transparent);
        if (size)
            *size = image.size();
        return image;
    }
};

inline QStringList expectedTopLevelRows()
{
    return {"New Tab", "New Private Tab", "New Window", "New Private Window", "-",
            "Bookmarks", "History", "-",
            "Find in Page…", "Print…", "Save Page As…", "-",
            "[row]", "-",
            "More Tools", "-",
            "Configure Kondor Browser…", "Help"};
}

inline QStringList expectedMoreToolsRows()
{
    return {"Developer Tools", "Save as PDF…", "Site Permissions…"};
}

inline QStringList expectedHelpRows()
{
    return {"Report a Bug…", "-", "About Kondor Browser"};
}

class MainMenuFixture : public QObject
{
protected:
    void registerMenuTypes()
    {
        QVERIFY(Database::instance()->isValid());
        qmlRegisterType<TabModel>("Kondor", 1, 0, "TabModel");
        registerSingleton<BookmarkManager>("BookmarkManager");
        registerSingleton<HistoryManager>("HistoryManager");
        registerSingleton<FaviconStore>("FaviconStore");
        registerSingleton<Settings>("Settings");
        registerSingleton<ProfileManager>("ProfileManager");
        m_engine.addImageProvider(QStringLiteral("kondor-favicon"), new EmptyImageProvider);
        previousMessageHandler() = qInstallMessageHandler(collectWarnings);
    }

    void openStubWindow()
    {
        collectedWarnings().clear();
        m_engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));
        QQmlComponent component(&m_engine);
        component.setData(kStubWindow,
                          QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR "/StubWindow.qml")));
        QObject *object = component.create();
        if (!object)
            qWarning() << component.errors();
        m_window = qobject_cast<QQuickWindow *>(object);
        QVERIFY(m_window);
        m_tabs = m_window->property("tabModel").value<TabModel *>();
        QVERIFY(m_tabs);
    }

    void showStubWindow()
    {
        m_tabs->addTab(false, QUrl(QStringLiteral("https://a.example")));
        m_window->show();
        m_window->requestActivate();
        QVERIFY(QTest::qWaitForWindowActive(m_window));
    }

    void evaluate(const QString &script)
    {
        QQmlExpression expression(qmlContext(m_window), m_window, script);
        expression.evaluate();
    }

    QStringList rowsOf(const QString &menuExpression)
    {
        const QString script = QStringLiteral(
            "(function(menu) { const rows = [];"
            " for (let i = 0; i < menu.count; ++i) { const it = menu.itemAt(i);"
            "   const kind = it.toString();"
            "   if (kind.indexOf('MenuSeparator') >= 0) rows.push('-');"
            "   else if (typeof it.text === 'string') rows.push(it.text);"
            "   else rows.push('[row]'); }"
            " return rows.join('|') })(%1)").arg(menuExpression);
        QQmlExpression expression(qmlContext(m_window), m_window, script);
        const QVariant value = expression.evaluate();
        if (expression.hasError())
            qWarning() << expression.error();
        return value.toString().split(QLatin1Char('|'));
    }

    static QStringList withoutSeparators(QStringList rows)
    {
        rows.removeAll(QStringLiteral("-"));
        return rows;
    }

    static QStringList sequencesIn(const QString &file, const QString &pattern)
    {
        QFile source(QStringLiteral(KONDOR_QML_DIR "/app/") + file);
        if (!source.open(QIODevice::ReadOnly))
            return {};
        QStringList sequences;
        const QString text = QString::fromUtf8(source.readAll());
        for (const QRegularExpressionMatch &match : QRegularExpression(pattern).globalMatch(text))
            sequences << match.captured(1);
        return sequences;
    }

    QQmlEngine m_engine;
    QQuickWindow *m_window = nullptr;
    TabModel *m_tabs = nullptr;
};
