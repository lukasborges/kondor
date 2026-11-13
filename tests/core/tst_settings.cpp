#include <QDateTime>
#include <QSettings>
#include <QStandardPaths>
#include <QTest>

#include "core/settings/settings.h"
#include "settingsharness.h"

class TestSettings : public QObject
{
    Q_OBJECT

private:
    void addSearchAndDownloadRows();
    void addStartupAndInterfaceRows();
    void addPrivacyRows();
    void addSpellCheckAndPasswordRows();
    static void verifySearchDefaults(Settings *settings);
    static void verifyDownloadDefaults(Settings *settings);
    static void verifyInterfaceDefaults(Settings *settings);
    static void verifyPrivacyDefaults(Settings *settings);

private slots:
    void initTestCase();
    void defaultValue_data();
    void defaultValue();
    void freshSettingsUseDefaults();
    void storageKeysStayTheSame_data();
    void storageKeysStayTheSame();
    void readerFontSizeIsClamped();
};

void TestSettings::initTestCase()
{
    QStandardPaths::setTestModeEnabled(true);
    QSettings settings(QStringLiteral("KDE"), QStringLiteral("Kondor"));
    settings.clear();
    settings.sync();
}

void TestSettings::addSearchAndDownloadRows()
{
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
}

void TestSettings::addStartupAndInterfaceRows()
{
    QTest::newRow("startupBehavior")
            << QStringLiteral("startupBehavior") << QVariant(QStringLiteral("homepage"));
    QTest::newRow("showBookmarksBar")
            << QStringLiteral("showBookmarksBar") << QVariant(false);
    QTest::newRow("showTopSites") << QStringLiteral("showTopSites") << QVariant(true);
    QTest::newRow("hiddenTopSites")
            << QStringLiteral("hiddenTopSites") << QVariant(QStringList());
}

void TestSettings::addPrivacyRows()
{
    QTest::newRow("clearDataOnExit")
            << QStringLiteral("clearDataOnExit") << QVariant(false);
    QTest::newRow("blockThirdPartyCookies")
            << QStringLiteral("blockThirdPartyCookies") << QVariant(false);
    QTest::newRow("searchSuggestions")
            << QStringLiteral("searchSuggestions") << QVariant(false);
}

void TestSettings::addSpellCheckAndPasswordRows()
{
    QTest::newRow("spellCheckEnabled")
            << QStringLiteral("spellCheckEnabled") << QVariant(true);
    QTest::newRow("offerToSavePasswords")
            << QStringLiteral("offerToSavePasswords") << QVariant(true);
    QTest::newRow("passwordNeverSaveSites")
            << QStringLiteral("passwordNeverSaveSites") << QVariant(QStringList());
    QTest::newRow("pinnedExtensions")
            << QStringLiteral("pinnedExtensions") << QVariant(QStringList());
    QTest::newRow("spellCheckLanguages")
            << QStringLiteral("spellCheckLanguages")
            << QVariant(QStringList{QStringLiteral("en-US")});
}

void TestSettings::defaultValue_data()
{
    QTest::addColumn<QString>("name");
    QTest::addColumn<QVariant>("expected");

    addSearchAndDownloadRows();
    addStartupAndInterfaceRows();
    addPrivacyRows();
    addSpellCheckAndPasswordRows();
}

void TestSettings::defaultValue()
{
    QFETCH(QString, name);
    QFETCH(QVariant, expected);

    QCOMPARE(Settings::instance()->defaultValue(name), expected);
}

void TestSettings::verifySearchDefaults(Settings *settings)
{
    QCOMPARE(settings->homePage(), settings->defaultValue(QStringLiteral("homePage")).toString());
    QCOMPARE(settings->searchEngine(),
             settings->defaultValue(QStringLiteral("searchEngine")).toString());
    QCOMPARE(settings->customSearchUrl(),
             settings->defaultValue(QStringLiteral("customSearchUrl")).toString());
    QCOMPARE(settings->searchSuggestions(),
             settings->defaultValue(QStringLiteral("searchSuggestions")).toBool());
}

void TestSettings::verifyDownloadDefaults(Settings *settings)
{
    QCOMPARE(settings->downloadDirectory(),
             settings->defaultValue(QStringLiteral("downloadDirectory")).toString());
    QCOMPARE(settings->askWhereToSave(),
             settings->defaultValue(QStringLiteral("askWhereToSave")).toBool());
}

void TestSettings::verifyInterfaceDefaults(Settings *settings)
{
    QCOMPARE(settings->startupBehavior(),
             settings->defaultValue(QStringLiteral("startupBehavior")).toString());
    QCOMPARE(settings->showBookmarksBar(),
             settings->defaultValue(QStringLiteral("showBookmarksBar")).toBool());
    QCOMPARE(settings->showTopSites(),
             settings->defaultValue(QStringLiteral("showTopSites")).toBool());
    QCOMPARE(settings->hiddenTopSites(),
             settings->defaultValue(QStringLiteral("hiddenTopSites")).toStringList());
}

void TestSettings::verifyPrivacyDefaults(Settings *settings)
{
    QCOMPARE(settings->clearDataOnExit(),
             settings->defaultValue(QStringLiteral("clearDataOnExit")).toBool());
    QCOMPARE(settings->blockThirdPartyCookies(),
             settings->defaultValue(QStringLiteral("blockThirdPartyCookies")).toBool());
}

void TestSettings::freshSettingsUseDefaults()
{
    Settings *settings = Settings::instance();
    verifySearchDefaults(settings);
    verifyDownloadDefaults(settings);
    verifyInterfaceDefaults(settings);
    verifyPrivacyDefaults(settings);
}

void TestSettings::storageKeysStayTheSame_data()
{
    QTest::addColumn<QString>("property");
    QTest::addColumn<QString>("key");
    QTest::addColumn<QVariant>("value");
    for (const StorageRow &row : kStorageRows)
        QTest::newRow(row.property) << QString::fromLatin1(row.property)
                                    << QString::fromLatin1(row.key) << row.value;
}

void TestSettings::storageKeysStayTheSame()
{
    QFETCH(QString, property);
    QFETCH(QString, key);
    QFETCH(QVariant, value);

    QVERIFY(Settings::instance()->setProperty(qPrintable(property), value));
    QSettings raw(QStringLiteral("KDE"), QStringLiteral("Kondor"));
    QCOMPARE(raw.value(key), value);
}

void TestSettings::readerFontSizeIsClamped()
{
    Settings::instance()->setReaderFontSize(100);
    QCOMPARE(Settings::instance()->readerFontSize(), 32);
    Settings::instance()->setReaderFontSize(1);
    QCOMPARE(Settings::instance()->readerFontSize(), 12);
}

QTEST_MAIN(TestSettings)
#include "tst_settings.moc"
