#include <QDateTime>
#include <QSettings>
#include <QStandardPaths>
#include <QTest>

#include "core/settings.h"

class TestSettings : public QObject
{
    Q_OBJECT

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

namespace {

struct StorageRow {
    const char *property;
    const char *key;
    QVariant value;
};

const QVariant kText(QStringLiteral("changed"));
const QVariant kList(QStringList{QStringLiteral("a.example")});

const QList<StorageRow> kStorageRows = {
    {"homePage", "General/HomePage", kText},
    {"searchEngine", "Search/Engine", kText},
    {"customSearchUrl", "Search/CustomUrl", kText},
    {"downloadDirectory", "Downloads/Directory", kText},
    {"askWhereToSave", "Downloads/AskWhereToSave", QVariant(true)},
    {"startupBehavior", "General/Startup", kText},
    {"showBookmarksBar", "UI/ShowBookmarksBar", QVariant(true)},
    {"showTopSites", "NewTab/ShowTopSites", QVariant(false)},
    {"hiddenTopSites", "NewTab/HiddenTopSites", kList},
    {"clearDataOnExit", "Privacy/ClearOnExit", QVariant(true)},
    {"blockThirdPartyCookies", "Privacy/BlockThirdPartyCookies", QVariant(true)},
    {"searchSuggestions", "Search/Suggestions", QVariant(true)},
    {"spellCheckEnabled", "SpellCheck/Enabled", QVariant(false)},
    {"spellCheckLanguages", "SpellCheck/Languages", kList},
    {"readerFontSize", "Reader/FontSize", QVariant(24)},
    {"readerSerif", "Reader/Serif", QVariant(false)},
    {"adBlockLastUpdate", "AdBlock/LastUpdate", QVariant(QDateTime::fromSecsSinceEpoch(1000000))},
    {"adBlockEnabled", "AdBlock/Enabled", QVariant(false)},
    {"adBlockAllowList", "AdBlock/AllowList", kList},
    {"offerToSavePasswords", "Passwords/OfferToSave", QVariant(false)},
    {"passwordNeverSaveSites", "Passwords/NeverSave", kList},
    {"extensionsAutoUpdate", "Extensions/AutoUpdate", QVariant(false)},
};

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
