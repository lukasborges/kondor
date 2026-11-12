#include "adblock/adblockmanager.h"
#include "core/settings.h"

#include <QSettings>
#include <QStandardPaths>
#include <QTest>

class TestAdBlockAllowList : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase()
    {
        QStandardPaths::setTestModeEnabled(true);
        QSettings(QStringLiteral("KDE"), QStringLiteral("Kondor")).clear();
    }

    void init()
    {
        Settings::instance()->setAdBlockAllowList({});
        manager()->setAllowed(QStringLiteral("example.org"), false, false);
        manager()->setAllowed(QStringLiteral("example.org"), false, true);
    }

    void sessionAllowDoesNotTouchSettings()
    {
        manager()->setAllowed(QStringLiteral("Example.org"), true, false);
        QVERIFY(manager()->isAllowed(QStringLiteral("example.org")));
        QVERIFY(Settings::instance()->adBlockAllowList().isEmpty());
    }

    void sessionBlockOverridesThePersistentList()
    {
        manager()->setAllowed(QStringLiteral("example.org"), true, true);
        manager()->setAllowed(QStringLiteral("example.org"), false, false);
        QVERIFY(!manager()->isAllowed(QStringLiteral("example.org")));
        QCOMPARE(Settings::instance()->adBlockAllowList(),
                 QStringList{QStringLiteral("example.org")});
    }

    void persistentChoiceReplacesTheSessionChoice()
    {
        manager()->setAllowed(QStringLiteral("example.org"), true, true);
        manager()->setAllowed(QStringLiteral("example.org"), false, false);
        manager()->setAllowed(QStringLiteral("example.org"), true, true);
        QVERIFY(manager()->isAllowed(QStringLiteral("example.org")));
    }

private:
    static AdBlockManager *manager() { return AdBlockManager::instance(); }
};

QTEST_MAIN(TestAdBlockAllowList)
#include "tst_adblockallowlist.moc"
