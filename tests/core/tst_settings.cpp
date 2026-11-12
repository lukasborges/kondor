#include <QSettings>
#include <QStandardPaths>
#include <QTest>

#include "settings.h"

class TestSettings : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void defaultValue_data();
    void defaultValue();
    void freshSettingsUseDefaults();
};

void TestSettings::initTestCase()
{
    QStandardPaths::setTestModeEnabled(true);
    // A fresh Settings must see an empty configuration file.
    QSettings settings(QStringLiteral("KDE"), QStringLiteral("Kondor"));
    settings.clear();
    settings.sync();
}

void TestSettings::defaultValue_data()
{
    QTest::addColumn<QString>("name");
    QTest::addColumn<QVariant>("expected");

    QTest::newRow("homePage") << QStringLiteral("homePage") << QVariant(QString());
    QTest::newRow("searchEngine")
            << QStringLiteral("searchEngine") << QVariant(QStringLiteral("duckduckgo"));
    QTest::newRow("customSearchUrl")
            << QStringLiteral("customSearchUrl") << QVariant(QString());
    QTest::newRow("downloadDirectory")
            << QStringLiteral("downloadDirectory")
            << QVariant(QStandardPaths::writableLocation(QStandardPaths::DownloadLocation));
    QTest::newRow("askWhereToSave")
            << QStringLiteral("askWhereToSave") << QVariant(false);
    QTest::newRow("startupBehavior")
            << QStringLiteral("startupBehavior") << QVariant(QStringLiteral("homepage"));
    QTest::newRow("showBookmarksBar")
            << QStringLiteral("showBookmarksBar") << QVariant(false);
    QTest::newRow("showTopSites") << QStringLiteral("showTopSites") << QVariant(true);
    QTest::newRow("hiddenTopSites")
            << QStringLiteral("hiddenTopSites") << QVariant(QStringList());
    QTest::newRow("clearDataOnExit")
            << QStringLiteral("clearDataOnExit") << QVariant(false);
    QTest::newRow("blockThirdPartyCookies")
            << QStringLiteral("blockThirdPartyCookies") << QVariant(false);
    QTest::newRow("searchSuggestions")
            << QStringLiteral("searchSuggestions") << QVariant(false);
    QTest::newRow("spellCheckEnabled")
            << QStringLiteral("spellCheckEnabled") << QVariant(true);
    QTest::newRow("offerToSavePasswords")
            << QStringLiteral("offerToSavePasswords") << QVariant(true);
    QTest::newRow("passwordNeverSaveSites")
            << QStringLiteral("passwordNeverSaveSites") << QVariant(QStringList());
    // No dictionaries in the test environment: falls back to US English.
    QTest::newRow("spellCheckLanguages")
            << QStringLiteral("spellCheckLanguages")
            << QVariant(QStringList{QStringLiteral("en-US")});
}

void TestSettings::defaultValue()
{
    QFETCH(QString, name);
    QFETCH(QVariant, expected);

    QCOMPARE(Settings::instance()->defaultValue(name), expected);
}

void TestSettings::freshSettingsUseDefaults()
{
    Settings *settings = Settings::instance();

    QCOMPARE(settings->homePage(), settings->defaultValue(QStringLiteral("homePage")).toString());
    QCOMPARE(settings->searchEngine(),
             settings->defaultValue(QStringLiteral("searchEngine")).toString());
    QCOMPARE(settings->customSearchUrl(),
             settings->defaultValue(QStringLiteral("customSearchUrl")).toString());
    QCOMPARE(settings->downloadDirectory(),
             settings->defaultValue(QStringLiteral("downloadDirectory")).toString());
    QCOMPARE(settings->askWhereToSave(),
             settings->defaultValue(QStringLiteral("askWhereToSave")).toBool());
    QCOMPARE(settings->startupBehavior(),
             settings->defaultValue(QStringLiteral("startupBehavior")).toString());
    QCOMPARE(settings->showBookmarksBar(),
             settings->defaultValue(QStringLiteral("showBookmarksBar")).toBool());
    QCOMPARE(settings->showTopSites(),
             settings->defaultValue(QStringLiteral("showTopSites")).toBool());
    QCOMPARE(settings->hiddenTopSites(),
             settings->defaultValue(QStringLiteral("hiddenTopSites")).toStringList());
    QCOMPARE(settings->clearDataOnExit(),
             settings->defaultValue(QStringLiteral("clearDataOnExit")).toBool());
    QCOMPARE(settings->blockThirdPartyCookies(),
             settings->defaultValue(QStringLiteral("blockThirdPartyCookies")).toBool());
    QCOMPARE(settings->searchSuggestions(),
             settings->defaultValue(QStringLiteral("searchSuggestions")).toBool());
}

QTEST_MAIN(TestSettings)
#include "tst_settings.moc"
