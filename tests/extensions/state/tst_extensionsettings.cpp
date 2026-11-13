#include <QTest>

#include "extensions/state/extensionsettings.h"

class TestExtensionSettings : public QObject
{
    Q_OBJECT

private slots:
    void sanitizesEachSettingType_data();
    void sanitizesEachSettingType();
    void clampsNumbersToMinAndMax_data();
    void clampsNumbersToMinAndMax();
};

namespace {

QVariantMap settingOf(const QString &type)
{
    return {{QStringLiteral("type"), type}, {QStringLiteral("default"), QStringLiteral("fallback")}};
}

QVariantMap boolSetting()
{
    return {{QStringLiteral("type"), QStringLiteral("bool")}, {QStringLiteral("default"), false}};
}

QVariantMap boolSettingDefaultingToTrue()
{
    return {{QStringLiteral("type"), QStringLiteral("bool")}, {QStringLiteral("default"), true}};
}

QVariantMap choiceSetting()
{
    QVariantMap setting = settingOf(QStringLiteral("choice"));
    setting.insert(QStringLiteral("choices"), QVariantList{QVariantMap{{QStringLiteral("value"), QStringLiteral("a")}}});
    return setting;
}

struct SettingCase {
    QVariantMap setting;
    QVariant value;
    QVariant expected;
};

void addRow(const char *name, const SettingCase &testCase)
{
    QTest::newRow(name) << testCase.setting << testCase.value << testCase.expected;
}

}

void TestExtensionSettings::sanitizesEachSettingType_data()
{
    QTest::addColumn<QVariantMap>("setting");
    QTest::addColumn<QVariant>("value");
    QTest::addColumn<QVariant>("expected");
    const QVariant fallback = QStringLiteral("fallback");
    const QVariantMap number = settingOf(QStringLiteral("number"));
    addRow("bool good", {boolSetting(), true, true});
    addRow("bool true text", {boolSetting(), QStringLiteral("true"), true});
    addRow("bool false text", {boolSettingDefaultingToTrue(), QStringLiteral("false"), false});
    addRow("bool bad", {boolSetting(), QStringLiteral("yes"), false});
    addRow("number good", {number, 5, 5.0});
    addRow("number bad", {number, QStringLiteral("x"), fallback});
    addRow("choice good", {choiceSetting(), QStringLiteral("a"), QStringLiteral("a")});
    addRow("choice bad", {choiceSetting(), QStringLiteral("z"), fallback});
    addRow("string good", {settingOf(QStringLiteral("string")), QStringLiteral("value"), QStringLiteral("value")});
    addRow("string bad", {settingOf(QStringLiteral("text")), 3, fallback});
    addRow("color bad", {settingOf(QStringLiteral("color")), true, fallback});
    addRow("keys good", {settingOf(QStringLiteral("keys")), QStringLiteral("k"), QStringLiteral("k")});
}

void TestExtensionSettings::sanitizesEachSettingType()
{
    QFETCH(QVariantMap, setting);
    QFETCH(QVariant, value);
    QFETCH(QVariant, expected);
    QCOMPARE(sanitizeSetting(setting, value), expected);
}

void TestExtensionSettings::clampsNumbersToMinAndMax_data()
{
    QTest::addColumn<double>("value");
    QTest::addColumn<double>("expected");
    QTest::newRow("above") << 500.0 << 100.0;
    QTest::newRow("below") << -5.0 << 0.0;
    QTest::newRow("inside") << 42.0 << 42.0;
}

void TestExtensionSettings::clampsNumbersToMinAndMax()
{
    QFETCH(double, value);
    QFETCH(double, expected);
    QVariantMap setting = settingOf(QStringLiteral("number"));
    setting.insert(QStringLiteral("min"), 0);
    setting.insert(QStringLiteral("max"), 100);
    QCOMPARE(sanitizeSetting(setting, value).toDouble(), expected);
}

QTEST_GUILESS_MAIN(TestExtensionSettings)
#include "tst_extensionsettings.moc"
