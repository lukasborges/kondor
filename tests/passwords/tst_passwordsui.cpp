#include <QQmlEngine>

#include "../extensions/extensionsuiharness.h"

class TestPasswordsUi : public QObject
{
    Q_OBJECT

private slots:
    void emptyListButtonRequestsAdd();

private:
    QQmlEngine m_engine;
};

void TestPasswordsUi::emptyListButtonRequestsAdd()
{
    QScopedPointer<QObject> window(createInWindow(&m_engine, emptySavedPasswordsQml));
    QVERIFY(window);
    auto *list = window->findChild<QQuickItem *>(QStringLiteral("savedPasswordsList"));
    QVERIFY(list);
    QQuickItem *button = nullptr;
    QTRY_VERIFY((button = itemWithText(list->parentItem(), QStringLiteral("Add Password…"))));
    clickCenterOf(button);
    QTRY_VERIFY(window->property("isAddRequested").toBool());
}

int runTestPasswordsUi(int argc, char *argv[])
{
    TestPasswordsUi test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_passwordsui.moc"
