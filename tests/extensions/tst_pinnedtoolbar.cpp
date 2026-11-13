#include <QAccessible>

#include "browser/tabs/tabmodel.h"
#include "extensionsuiharness.h"

namespace {

constexpr const char *toolBarWindowQml =
    "import QtQuick\nimport QtQuick.Controls\nimport Kondor\n"
    "ApplicationWindow {\n"
    "    visible: true\n"
    "    width: 700; height: 100\n"
    "    ExtensionsToolButtons { tabs: theTabs; browserWindow: null }\n"
    "}\n";

QString accessibleNameOf(QQuickItem *item)
{
    QAccessibleInterface *accessible = QAccessible::queryAccessibleInterface(item);
    return accessible ? accessible->text(QAccessible::Name) : QString();
}

QQuickItem *pinnedButtonNamed(QQuickItem *root, const QString &name)
{
    if (root->isVisible() && accessibleNameOf(root) == name)
        return root;
    for (QQuickItem *child : root->childItems())
        if (QQuickItem *found = pinnedButtonNamed(child, name))
            return found;
    return nullptr;
}

}

class TestPinnedToolBar : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase()
    {
        QVERIFY(m_work.isValid());
        QAccessible::setActive(true);
        qmlRegisterType<TabModel>("Kondor", 1, 0, "TabModel");
    }
    void cleanup();
    void pinnedExtensionShowsVisibleButton();
    void unpinRemovesButton();
    void pinnedButtonOpensPanelOnExtension();

private:
    QQuickItem *buttonOf(const QString &name) const;
    void showToolBar();
    bool isPinnedButtonLaidOut() const;

    QTemporaryDir m_work;
    QQmlEngine m_engine;
    TabModel m_tabs;
    QScopedPointer<QObject> m_window;
};

void TestPinnedToolBar::cleanup()
{
    m_window.reset();
    ExtensionManager::instance()->setPinned(QStringLiteral("sample"), false);
    removeEveryExtension();
}

void TestPinnedToolBar::showToolBar()
{
    QVERIFY(installSample(m_work.path()));
    m_tabs.addTab(false, QUrl(QStringLiteral("https://www.example.com/page")));
    m_engine.rootContext()->setContextProperty(QStringLiteral("theTabs"), &m_tabs);
    m_window.reset(createInWindow(&m_engine, toolBarWindowQml));
    QVERIFY(m_window);
    QVERIFY(QTest::qWaitForWindowExposed(qobject_cast<QQuickWindow *>(m_window.data())));
}

QQuickItem *TestPinnedToolBar::buttonOf(const QString &name) const
{
    auto *window = qobject_cast<QQuickWindow *>(m_window.data());
    return pinnedButtonNamed(window->contentItem(), name);
}

bool TestPinnedToolBar::isPinnedButtonLaidOut() const
{
    QQuickItem *button = buttonOf(QStringLiteral("Sample Extension"));
    QQuickItem *extensionsButton = findByName(m_window.data(), "extensionsButton");
    return button && extensionsButton && extensionsButton->x() >= button->width();
}

void TestPinnedToolBar::pinnedExtensionShowsVisibleButton()
{
    showToolBar();
    ExtensionManager::instance()->setPinned(QStringLiteral("sample"), true);
    QTRY_VERIFY(buttonOf(QStringLiteral("Sample Extension")));
    QQuickItem *button = buttonOf(QStringLiteral("Sample Extension"));
    QVERIFY(button->width() > 0);
    QVERIFY(button->height() > 0);
}

void TestPinnedToolBar::unpinRemovesButton()
{
    showToolBar();
    ExtensionManager::instance()->setPinned(QStringLiteral("sample"), true);
    QTRY_VERIFY(buttonOf(QStringLiteral("Sample Extension")));
    ExtensionManager::instance()->setPinned(QStringLiteral("sample"), false);
    QTRY_VERIFY(!buttonOf(QStringLiteral("Sample Extension")));
}

void TestPinnedToolBar::pinnedButtonOpensPanelOnExtension()
{
    showToolBar();
    ExtensionManager::instance()->setPinned(QStringLiteral("sample"), true);
    QTRY_VERIFY(isPinnedButtonLaidOut());
    clickCenterOf(buttonOf(QStringLiteral("Sample Extension")));
    QObject *panel = m_window->findChild<QObject *>(QStringLiteral("extensionsPanel"));
    QVERIFY(panel);
    QTRY_COMPARE(panel->property("currentId").toString(), QStringLiteral("sample"));
}

int runTestPinnedToolBar(int argc, char *argv[])
{
    TestPinnedToolBar test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_pinnedtoolbar.moc"
