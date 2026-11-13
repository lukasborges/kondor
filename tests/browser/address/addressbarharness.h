#pragma once

#include <QDateTime>
#include <QJSEngine>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickItem>
#include <QQuickWindow>
#include <QSqlQuery>
#include <QTest>

#include "adblock/adblockmanager.h"
#include "bookmarks/bookmarkmanager.h"
#include "browser/favicons/faviconstore.h"
#include "browser/profile/profilemanager.h"
#include "browser/address/searchsuggestions.h"
#include "browser/tabs/tab.h"
#include "browser/tabs/tabmodel.h"
#include "../../common/qmltesthelpers.h"
#include "core/database/database.h"
#include "core/settings/settings.h"
#include "history/historymanager.h"

inline void registerAddressBarTypes()
{
    qmlRegisterType<TabModel>("Kondor", 1, 0, "TabModel");
    qmlRegisterUncreatableType<Tab>("Kondor", 1, 0, "Tab", QStringLiteral("Created by TabModel"));
    registerSingleton<ProfileManager>("ProfileManager");
    registerSingleton<HistoryManager>("HistoryManager");
    registerSingleton<BookmarkManager>("BookmarkManager");
    registerSingleton<FaviconStore>("FaviconStore");
    registerSingleton<Settings>("Settings");
    registerSingleton<SearchSuggestions>("SearchSuggestions");
    registerSingleton<AdBlockManager>("AdBlockManager");
}

class AddressBarHarness
{
public:
    explicit AddressBarHarness(QQmlEngine &sharedEngine) : engine(sharedEngine) {}

    ~AddressBarHarness()
    {
        delete window;
        delete tabs;
    }

    bool open()
    {
        engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));
        tabs = new TabModel;
        tabs->addTab(false, QUrl(QStringLiteral("https://kde.org/one")));
        QQmlComponent component(&engine, QUrl::fromLocalFile(QStringLiteral(
            KONDOR_TEST_DATA_DIR "/AddressBarHost.qml")));
        window = qobject_cast<QQuickWindow *>(component.createWithInitialProperties(
            { { QStringLiteral("tabModel"), QVariant::fromValue(tabs) } }));
        return window && QTest::qWaitForWindowExposed(window);
    }

    QQuickItem *bar() const { return window->property("addressBar").value<QQuickItem *>(); }
    QString text() const { return bar()->property("text").toString(); }

    QObject *suggestions() const
    {
        for (QObject *child : bar()->children()) {
            if (child->property("networkSuggestions").isValid())
                return child;
        }
        return nullptr;
    }

    QString textOfRow(int index) const
    {
        QVariant selected;
        QMetaObject::invokeMethod(suggestions(), "selectedText", Q_RETURN_ARG(QVariant, selected),
                                  Q_ARG(QVariant, index));
        return selected.toString();
    }

    void type(const QString &typed)
    {
        bar()->forceActiveFocus();
        QTRY_VERIFY(bar()->hasActiveFocus());
        for (const QChar letter : typed)
            QTest::keyClick(window, letter.toLatin1());
    }

    void press(Qt::Key key) { QTest::keyClick(window, key); }

    QQmlEngine &engine;
    QQuickWindow *window = nullptr;
    TabModel *tabs = nullptr;
};

inline bool addHistoryVisit(const QString &url)
{
    QSqlQuery insert(Database::instance()->handle());
    insert.prepare(QStringLiteral("INSERT INTO history (url, title, visited_at) VALUES (?, ?, ?)"));
    insert.addBindValue(url);
    insert.addBindValue(QStringLiteral("Plasma"));
    insert.addBindValue(QDateTime::currentSecsSinceEpoch());
    return insert.exec();
}
