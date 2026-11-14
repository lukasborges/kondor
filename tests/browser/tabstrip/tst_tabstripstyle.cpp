#include "tabstripharness.h"

class TestTabStripStyle : public TabStripFixture
{
    Q_OBJECT

private slots:
    void initTestCase() { registerTabStripTypes(); }
    void init() { setUpStrip(); }
    void cleanup() { tearDownStrip(); }
    void classicKeepsTheStyleBackgroundVisible();
    void styledHidesTheStyleBackground();
    void classicBackgroundSurvivesSwitchingStyles();

private:
    void useStyle(const QString &style);
    QQuickItem *backgroundOf(int index) const;
};

void TestTabStripStyle::useStyle(const QString &style)
{
    m_strip->setProperty("tabStyle", style);
    QTest::qWait(50);
}

QQuickItem *TestTabStripStyle::backgroundOf(int index) const
{
    return itemAt(index)->property("background").value<QQuickItem *>();
}

void TestTabStripStyle::classicKeepsTheStyleBackgroundVisible()
{
    useStyle(QStringLiteral("classic"));
    addTabs(3);
    QVERIFY(backgroundOf(0)->isVisible());
    QCOMPARE(backgroundOf(0)->parentItem(), itemAt(0));
}

void TestTabStripStyle::styledHidesTheStyleBackground()
{
    useStyle(QStringLiteral("floating"));
    addTabs(3);
    QVERIFY(!backgroundOf(0)->isVisible());
}

void TestTabStripStyle::classicBackgroundSurvivesSwitchingStyles()
{
    addTabs(3);
    QQuickItem *original = backgroundOf(0);
    for (const QString &style : { QStringLiteral("classic"), QStringLiteral("floating"),
                                  QStringLiteral("classic") })
        useStyle(style);
    QCOMPARE(backgroundOf(0), original);
    QVERIFY(original->isVisible());
    QCOMPARE(original->parentItem(), itemAt(0));
}

int runTabStripStyle(int argc, char *argv[])
{
    TestTabStripStyle test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_tabstripstyle.moc"
