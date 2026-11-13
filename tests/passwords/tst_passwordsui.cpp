#include <QQmlEngine>

#include "../extensions/extensionsuiharness.h"

class TestPasswordsUi : public QObject
{
    Q_OBJECT

private slots:
    void emptyListButtonRequestsAdd();
    void rowClickFillsAndCloses();
    void copyButtonShowsCheckMarkAndStaysOpen();
    void downKeyMovesToNextRow();

private:
    QObject *openPopup();
    QList<QQuickItem *> rows() const;

    QQmlEngine m_engine;
    QScopedPointer<QObject> m_window;
};

namespace {
void collectNamed(QQuickItem *root, const QString &name, QList<QQuickItem *> &found)
{
    if (root->objectName() == name)
        found.append(root);
    for (QQuickItem *child : root->childItems())
        collectNamed(child, name, found);
}
}

QObject *TestPasswordsUi::openPopup()
{
    m_window.reset(createInWindow(&m_engine, savedPasswordsPopupQml));
    QObject *popup = m_window ? childObject(m_window.data(), "popup") : nullptr;
    if (popup)
        QMetaObject::invokeMethod(popup, "open");
    return popup;
}

QList<QQuickItem *> TestPasswordsUi::rows() const
{
    QList<QQuickItem *> found;
    auto *popup = childObject(m_window.data(), "popup");
    collectNamed(popup->property("contentItem").value<QQuickItem *>(),
                 QStringLiteral("savedAccountRow"), found);
    return found;
}

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

void TestPasswordsUi::rowClickFillsAndCloses()
{
    QObject *popup = openPopup();
    QVERIFY(popup);
    QTRY_COMPARE(rows().size(), 2);
    QTRY_VERIFY(popup->property("opened").toBool());

    clickCenterOf(rows().at(1)->childItems().first());

    QTRY_COMPARE(m_window->property("filledUsername").toString(), QStringLiteral("bruno"));
    QTRY_VERIFY(!popup->property("opened").toBool());
}

void TestPasswordsUi::copyButtonShowsCheckMarkAndStaysOpen()
{
    QObject *popup = openPopup();
    QVERIFY(popup);
    QTRY_COMPARE(rows().size(), 2);
    QTRY_VERIFY(popup->property("opened").toBool());
    QList<QQuickItem *> buttons;
    collectNamed(rows().first(), QStringLiteral("copyPasswordButton"), buttons);
    QVERIFY(!buttons.isEmpty());

    QMetaObject::invokeMethod(buttons.first(), "click");

    QTRY_VERIFY(buttons.first()->property("isCopied").toBool());
    QVERIFY(popup->property("opened").toBool());
}

void TestPasswordsUi::downKeyMovesToNextRow()
{
    QObject *popup = openPopup();
    QVERIFY(popup);
    QTRY_COMPARE(rows().size(), 2);
    QTRY_VERIFY(rows().first()->hasActiveFocus());

    QTest::keyClick(qobject_cast<QQuickWindow *>(m_window.data()), Qt::Key_Down);

    QTRY_VERIFY(rows().at(1)->hasActiveFocus());
}

int runTestPasswordsUi(int argc, char *argv[])
{
    TestPasswordsUi test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_passwordsui.moc"
