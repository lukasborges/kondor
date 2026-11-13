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


constexpr int toolBarIconBoxSize = 22;

QSize paintedBoundsOf(const QImage &image)
{
    const QRgb background = image.pixel(0, 0);
    QRect bounds;
    for (int y = 0; y < image.height(); ++y)
        for (int x = 0; x < image.width(); ++x)
            if (image.pixel(x, y) != background)
                bounds |= QRect(x, y, 1, 1);
    return bounds.size();
}

QSize iconSizeOf(QQuickItem *button)
{
    const QRectF area = button->mapRectToScene(button->boundingRect());
    const QImage window = button->window()->grabWindow();
    return paintedBoundsOf(window.copy(area.toAlignedRect()));
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
    void pinnedFileIconFitsToolBarIconBox();
    void pinnedThemeIconHasExtensionsButtonIconSize();

private:
    QQuickItem *buttonOf(const QString &name) const;
    void showToolBar();
    bool installThemeIconSample();
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
    if (ExtensionManager::instance()->count() == 0)
        QVERIFY(installSample(m_work.path()));
    m_tabs.addTab(false, QUrl(QStringLiteral("https://www.example.com/page")));
    m_engine.rootContext()->setContextProperty(QStringLiteral("theTabs"), &m_tabs);
    m_window.reset(createInWindow(&m_engine, toolBarWindowQml));
    QVERIFY(m_window);
    QVERIFY(QTest::qWaitForWindowExposed(qobject_cast<QQuickWindow *>(m_window.data())));
}

bool TestPinnedToolBar::installThemeIconSample()
{
    const QString zip = packVariant(m_work.path(), QStringLiteral("theme"), [](QJsonObject &manifest) {
        manifest.insert(QStringLiteral("icon"), QStringLiteral("plugins"));
    });
    return ExtensionManager::instance()->installPackage({zip, QStringLiteral("file")}, QStringLiteral("sample")).isInstalled;
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

void TestPinnedToolBar::pinnedFileIconFitsToolBarIconBox()
{
    showToolBar();
    ExtensionManager::instance()->setPinned(QStringLiteral("sample"), true);
    QTRY_VERIFY(isPinnedButtonLaidOut());
    const QSize painted = iconSizeOf(buttonOf(QStringLiteral("Sample Extension")));
    QVERIFY(!painted.isEmpty());
    QVERIFY(painted.width() <= toolBarIconBoxSize && painted.height() <= toolBarIconBoxSize);
}

void TestPinnedToolBar::pinnedThemeIconHasExtensionsButtonIconSize()
{
    QVERIFY(installThemeIconSample());
    showToolBar();
    ExtensionManager::instance()->setPinned(QStringLiteral("sample"), true);
    QTRY_VERIFY(isPinnedButtonLaidOut());
    QCOMPARE(iconSizeOf(buttonOf(QStringLiteral("Sample Extension"))),
             iconSizeOf(findByName(m_window.data(), "extensionsButton")));
    QCOMPARE(buttonOf(QStringLiteral("Sample Extension"))->width(),
             findByName(m_window.data(), "extensionsButton")->width());
}

int runTestPinnedToolBar(int argc, char *argv[])
{
    TestPinnedToolBar test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_pinnedtoolbar.moc"
