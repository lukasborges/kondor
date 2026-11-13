#include <QAccessible>

#include "common/accessibilitywalk.h"
#include "tabstripharness.h"

class TestTabStripAccessibility : public TabStripFixture
{
    Q_OBJECT

private slots:
    void initTestCase()
    {
        registerTabStripTypes();
        QAccessible::setActive(true);
    }
    void init() { setUpStrip(); }
    void cleanup() { tearDownStrip(); }
    void everyVisibleButtonHasAName();
};

void TestTabStripAccessibility::everyVisibleButtonHasAName()
{
    addTabs(20);
    QVERIFY(button("scrollLeftButton")->isVisible());
    QCOMPARE(unnamedButtons(m_strip), QStringList());
}

int runTabStripAccessibility(int argc, char *argv[])
{
    TestTabStripAccessibility test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_tabstripaccessibility.moc"
