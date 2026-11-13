#include <memory>

#include "extensionsuiharness.h"

class TestExtensionsUi : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanup();
    void extensionsPageListsInstalled();
    void emptyListButtonOpensCatalog();

private:
    QTemporaryDir m_work;
    QQmlEngine m_engine;
    QScopedPointer<QObject> m_window;
};

void TestExtensionsUi::initTestCase()
{
    QVERIFY(m_work.isValid());
}

void TestExtensionsUi::cleanup()
{
    m_window.reset();
    removeEveryExtension();
}

void TestExtensionsUi::extensionsPageListsInstalled()
{
    m_window.reset(createInWindow(&m_engine, extensionsPageQml));
    QVERIFY(m_window);
    QQuickItem *list = m_window->findChild<QQuickItem *>(QStringLiteral("extensionList"));
    QVERIFY(list);
    QCOMPARE(list->property("count").toInt(), 0);
    QVERIFY(installSample(m_work.path()));
    QTRY_COMPARE(list->property("count").toInt(), 1);
    ExtensionManager::instance()->setEnabled(QStringLiteral("sample"), false);
    QQuickItem *row = nullptr;
    QTRY_VERIFY2((QMetaObject::invokeMethod(list, "itemAtIndex", Q_RETURN_ARG(QQuickItem *, row),
                                            Q_ARG(int, 0)), row), "the row was not created");
    QVERIFY(row->isEnabled());
}

void TestExtensionsUi::emptyListButtonOpensCatalog()
{
    m_window.reset(createInWindow(&m_engine, extensionsPageQml));
    QVERIFY(m_window);
    auto *list = m_window->findChild<QQuickItem *>(QStringLiteral("extensionList"));
    QVERIFY(list);
    QQuickItem *button = nullptr;
    QTRY_VERIFY((button = itemWithText(list->parentItem(), QStringLiteral("Get New Extensions…"))));
    clickCenterOf(button);
    QTRY_VERIFY(isDialogOpen(m_window.data(), QStringLiteral("Get New Extensions")));
}

int runTestExtensionsUi(int argc, char *argv[])
{
    TestExtensionsUi test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensionsui.moc"
