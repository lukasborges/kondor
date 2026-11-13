#include <QAccessible>

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

private:
    static bool isUnnamedButton(QQuickItem *item);
    static QStringList unnamedButtons(QQuickItem *root);
};

bool TestTabStripAccessibility::isUnnamedButton(QQuickItem *item)
{
    if (!item->isVisible() || !item->inherits("QQuickAbstractButton"))
        return false;
    QAccessibleInterface *accessible = QAccessible::queryAccessibleInterface(item);
    return accessible && accessible->text(QAccessible::Name).isEmpty();
}

QStringList TestTabStripAccessibility::unnamedButtons(QQuickItem *root)
{
    QStringList found;
    if (isUnnamedButton(root))
        found << QString::fromLatin1(root->metaObject()->className());
    for (QQuickItem *child : root->childItems())
        found << unnamedButtons(child);
    return found;
}

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
