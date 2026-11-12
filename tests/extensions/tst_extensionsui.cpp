#include <memory>

#include "extensionsuiharness.h"

class TestExtensionsUi : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanup();
    void menuListsHeaderToggleAndRunOnSite();
    void siteTurnedOffShowsUnchecked();
    void privateTabListsOnlyAllowedExtensions();
    void extensionsPageListsInstalled();

private:
    void openMenu();

    QTemporaryDir m_work;
    QQmlEngine m_engine;
    std::unique_ptr<Tab> m_tab;
    QScopedPointer<QObject> m_window;
    QObject *m_menu = nullptr;
};

void TestExtensionsUi::initTestCase()
{
    QVERIFY(m_work.isValid());
}

void TestExtensionsUi::cleanup()
{
    m_window.reset();
    m_tab.reset();
    m_engine.rootContext()->setContextProperty(QStringLiteral("theTab"), nullptr);
    removeEveryExtension();
}

void TestExtensionsUi::openMenu()
{
    QVERIFY(installSample(m_work.path()));
    m_tab.reset(new Tab(nullptr));
    m_tab->setUrl(QUrl(QStringLiteral("https://www.example.com/page")));
    m_tab->extensionItems()->setChecked(QStringLiteral("sample"), QStringLiteral("toggle"), true);
    m_engine.rootContext()->setContextProperty(QStringLiteral("theTab"), m_tab.get());
    m_window.reset(createInWindow(&m_engine, menuWindowQml));
    QVERIFY(m_window);
    m_menu = childObject(m_window.data(), "menu");
    QVERIFY(m_menu);
}

void TestExtensionsUi::menuListsHeaderToggleAndRunOnSite()
{
    openMenu();
    const QVariantList entries = rebuiltEntries(m_menu);
    QCOMPARE(entries.size(), 3);
    QCOMPARE(textOf(entries.at(0), QStringLiteral("kind")), QStringLiteral("header"));
    QCOMPARE(textOf(entries.at(0), QStringLiteral("title")), QStringLiteral("Sample Extension"));
    QCOMPARE(textOf(entries.at(1), QStringLiteral("title")), QStringLiteral("Toggle Mark"));
    QVERIFY(isChecked(entries.at(1)));
    QCOMPARE(textOf(entries.at(2), QStringLiteral("title")), QStringLiteral("Run on www.example.com"));
    QVERIFY(isChecked(entries.at(2)));
}

void TestExtensionsUi::siteTurnedOffShowsUnchecked()
{
    openMenu();
    ExtensionManager::instance()->setSiteEnabled(QStringLiteral("sample"), m_tab->url(), false);
    QVERIFY(!isChecked(rebuiltEntries(m_menu).at(2)));
}

void TestExtensionsUi::privateTabListsOnlyAllowedExtensions()
{
    openMenu();
    QQuickWebEngineProfile privateProfile;
    Tab privateTab(&privateProfile);
    privateTab.setUrl(QUrl(QStringLiteral("https://www.example.com/page")));
    m_engine.rootContext()->setContextProperty(QStringLiteral("theTab"), &privateTab);
    m_menu->setProperty("tab", QVariant::fromValue(&privateTab));
    QCOMPARE(rebuiltEntries(m_menu).size(), 0);
    allowInPrivateWindows(QStringLiteral("sample"));
    QCOMPARE(rebuiltEntries(m_menu).size(), 2);
    m_window.reset();
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

int runTestExtensionsUi(int argc, char *argv[])
{
    TestExtensionsUi test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensionsui.moc"
