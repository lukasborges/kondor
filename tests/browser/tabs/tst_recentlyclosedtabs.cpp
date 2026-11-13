#include <QSignalSpy>
#include <QTest>

#include "browser/profilemanager.h"
#include "browser/tab.h"
#include "browser/tabmodel.h"
#include "tabmodelharness.h"

class TestRecentlyClosedTabs : public QObject
{
    Q_OBJECT

private slots:
    void reopenClosedTabRestoresPosition();
    void privateTabsAreNotReopened();
    void recentlyClosedListsNewestFirst();
    void reopenClosedTabByIndex();
    void privateTabsAreNotInRecentlyClosed();
    void recentlyClosedKeepsAtMostTheLimit();
};

void TestRecentlyClosedTabs::reopenClosedTabRestoresPosition()
{
    TabModel model;
    model.addTab(false, QUrl(QStringLiteral("https://a.example")));
    model.addTab(false, QUrl(QStringLiteral("https://b.example")));
    model.addTab(false, QUrl(QStringLiteral("https://c.example")));
    QVERIFY(!model.canReopenClosedTab());

    model.closeTab(1);
    QCOMPARE(model.count(), 2);
    QVERIFY(model.canReopenClosedTab());

    model.reopenClosedTab();
    QCOMPARE(model.count(), 3);
    QCOMPARE(model.currentIndex(), 1);
    QCOMPARE(model.currentTab()->url(), QUrl(QStringLiteral("https://b.example")));
    QVERIFY(!model.canReopenClosedTab());
}

void TestRecentlyClosedTabs::privateTabsAreNotReopened()
{
    TabModel model;
    model.addTab(false, QUrl(QStringLiteral("https://a.example")));
    model.addTab(true, QUrl(QStringLiteral("https://private.example")));

    model.closeTab(1);
    QCOMPARE(model.count(), 1);
    QVERIFY(!model.canReopenClosedTab());

    model.reopenClosedTab();
    QCOMPARE(model.count(), 1);
}

void TestRecentlyClosedTabs::recentlyClosedListsNewestFirst()
{
    TabModel model;
    QSignalSpy spy(&model, &TabModel::recentlyClosedChanged);
    model.addTab(false, QUrl(QStringLiteral("https://a.example")));
    model.addTab(false, QUrl(QStringLiteral("https://b.example")));
    model.addTab(false, QUrl(QStringLiteral("https://c.example")));
    QVERIFY(model.recentlyClosed().isEmpty());

    model.closeTab(0);
    model.closeTab(1);
    QCOMPARE(spy.count(), 2);

    const QVariantList closed = model.recentlyClosed();
    QCOMPARE(closed.size(), 2);
    QCOMPARE(closed.at(0).toMap().value(QStringLiteral("url")).toUrl(),
             QUrl(QStringLiteral("https://c.example")));
    QCOMPARE(closed.at(1).toMap().value(QStringLiteral("url")).toUrl(),
             QUrl(QStringLiteral("https://a.example")));
}

void TestRecentlyClosedTabs::reopenClosedTabByIndex()
{
    TabModel model;
    model.addTab(false, QUrl(QStringLiteral("https://a.example")));
    model.addTab(false, QUrl(QStringLiteral("https://b.example")));
    model.addTab(false, QUrl(QStringLiteral("https://c.example")));
    model.closeTab(0);
    model.closeTab(1);

    model.reopenClosedTab(1);
    QCOMPARE(model.currentTab()->url(), QUrl(QStringLiteral("https://a.example")));
    QCOMPARE(model.recentlyClosed().size(), 1);
    QCOMPARE(model.recentlyClosed().at(0).toMap().value(QStringLiteral("url")).toUrl(),
             QUrl(QStringLiteral("https://c.example")));

    model.reopenClosedTab(5);
    QCOMPARE(model.recentlyClosed().size(), 1);
}

void TestRecentlyClosedTabs::privateTabsAreNotInRecentlyClosed()
{
    TabModel model;
    model.addTab(false, QUrl(QStringLiteral("https://a.example")));
    model.addTab(true, QUrl(QStringLiteral("https://private.example")));
    model.closeTab(1);
    QVERIFY(model.recentlyClosed().isEmpty());
}

void TestRecentlyClosedTabs::recentlyClosedKeepsAtMostTheLimit()
{
    TabModel model;
    for (int i = 0; i < 25; ++i)
        model.addTab(false, QUrl(QStringLiteral("https://site%1.example/").arg(i)));
    for (int i = 0; i < 25; ++i)
        model.closeTab(0);

    const QVariantList closed = model.recentlyClosed();
    QCOMPARE(closed.size(), 20);
    QCOMPARE(closed.first().toMap().value(QStringLiteral("url")).toUrl(),
             QUrl(QStringLiteral("https://site24.example/")));
}

int runRecentlyClosedTabs(int argc, char *argv[])
{
    TestRecentlyClosedTabs test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_recentlyclosedtabs.moc"
