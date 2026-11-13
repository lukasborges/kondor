#include <QKeySequence>
#include <QTest>

#include "extensions/action/actionitemdisplay.h"

class TestActionItemDisplay : public QObject
{
    Q_OBJECT

private slots:
    void shortcutShowsCurrentKeysValue();
    void itemWithoutKeysSettingHasNoShortcut();
    void unparsableKeysValueHasNoShortcut();
    void missingThemeIconIsDropped();
    void iconPathOrUrlIsDropped();
};

namespace {

QVariantMap displayedItem(const QVariantMap &item, const QVariantMap &values = {})
{
    return ActionItemDisplay::forDisplay({item}, values).constFirst().toMap();
}

QVariantMap keyedItem()
{
    return {{QStringLiteral("keysSetting"), QStringLiteral("keyFaster")}};
}

QVariantMap valueOf(const QString &keys)
{
    return {{QStringLiteral("keyFaster"), keys}};
}

QVariantMap itemWithIcon(const QString &icon)
{
    return {{QStringLiteral("icon"), icon}};
}

}

void TestActionItemDisplay::shortcutShowsCurrentKeysValue()
{
    const QString expected = QKeySequence(QStringLiteral("Ctrl+S")).toString(QKeySequence::NativeText);
    QCOMPARE(displayedItem(keyedItem(), valueOf(QStringLiteral("Ctrl+S"))).value(QStringLiteral("shortcut")).toString(), expected);
}

void TestActionItemDisplay::itemWithoutKeysSettingHasNoShortcut()
{
    QVERIFY(displayedItem({}, valueOf(QStringLiteral("S"))).value(QStringLiteral("shortcut")).toString().isEmpty());
}

void TestActionItemDisplay::unparsableKeysValueHasNoShortcut()
{
    QVERIFY(displayedItem(keyedItem(), valueOf(QStringLiteral("Ctrl+NoSuchKey"))).value(QStringLiteral("shortcut")).toString().isEmpty());
    QVERIFY(displayedItem(keyedItem(), valueOf(QString())).value(QStringLiteral("shortcut")).toString().isEmpty());
}

void TestActionItemDisplay::missingThemeIconIsDropped()
{
    QVERIFY(displayedItem(itemWithIcon(QStringLiteral("no-such-icon-anywhere"))).value(QStringLiteral("icon")).toString().isEmpty());
}

void TestActionItemDisplay::iconPathOrUrlIsDropped()
{
    const QStringList sources{QStringLiteral("/tmp/x.png"), QStringLiteral("file:///tmp/x.png"),
                              QStringLiteral("https://example.com/x.png")};
    for (const QString &source : sources)
        QVERIFY(displayedItem(itemWithIcon(source)).value(QStringLiteral("icon")).toString().isEmpty());
}

QTEST_GUILESS_MAIN(TestActionItemDisplay)
#include "tst_actionitemdisplay.moc"
