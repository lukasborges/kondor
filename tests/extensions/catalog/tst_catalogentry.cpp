#include <QJsonArray>
#include <QTest>

#include "extensions/catalogentry.h"

class TestCatalogEntry : public QObject
{
    Q_OBJECT

private slots:
    void resolvesRelativePackageAndIconUrls();
    void skipsEntriesWithoutIdVersionOrPackage_data();
    void skipsEntriesWithoutIdVersionOrPackage();
    void keepsIconNamesAsTheyAre();
};

namespace {

const QUrl kCatalogUrl(QStringLiteral("https://example.com/catalog/catalog.json"));

QJsonObject entryJson()
{
    return {{QStringLiteral("id"), QStringLiteral("sample")},
            {QStringLiteral("version"), QStringLiteral("1.0.0")},
            {QStringLiteral("package"), QStringLiteral("packages/sample.kondorext")},
            {QStringLiteral("sha256"), QStringLiteral("ABCDEF")}};
}

QJsonObject withField(const QString &key, const QJsonValue &value)
{
    QJsonObject object = entryJson();
    object.insert(key, value);
    return object;
}

}

void TestCatalogEntry::resolvesRelativePackageAndIconUrls()
{
    const auto entry = parseCatalogEntry(withField(QStringLiteral("icon"), QStringLiteral("icons/sample.svg")),
                                         kCatalogUrl);
    QVERIFY(entry);
    QCOMPARE(entry->package.toString(), QStringLiteral("https://example.com/catalog/packages/sample.kondorext"));
    QCOMPARE(entry->iconSource, QStringLiteral("https://example.com/catalog/icons/sample.svg"));
    QCOMPARE(entry->sha256, QStringLiteral("abcdef"));
}

void TestCatalogEntry::skipsEntriesWithoutIdVersionOrPackage_data()
{
    QTest::addColumn<QString>("missing");
    QTest::newRow("id") << QStringLiteral("id");
    QTest::newRow("version") << QStringLiteral("version");
    QTest::newRow("package") << QStringLiteral("package");
}

void TestCatalogEntry::skipsEntriesWithoutIdVersionOrPackage()
{
    QFETCH(QString, missing);
    QJsonObject object = entryJson();
    object.remove(missing);
    QVERIFY(!parseCatalogEntry(object, kCatalogUrl));
    QJsonArray extensions{object, entryJson()};
    const QJsonObject root{{QStringLiteral("version"), 1}, {QStringLiteral("extensions"), extensions}};
    QString error;
    const auto entries = parseCatalog(QJsonDocument(root).toJson(), kCatalogUrl, error);
    QVERIFY(entries);
    QCOMPARE(entries->size(), 1);
}

void TestCatalogEntry::keepsIconNamesAsTheyAre()
{
    const auto named = parseCatalogEntry(withField(QStringLiteral("icon"), QStringLiteral("dark-mode")), kCatalogUrl);
    QCOMPARE(named->iconSource, QStringLiteral("dark-mode"));
    const auto none = parseCatalogEntry(entryJson(), kCatalogUrl);
    QCOMPARE(none->iconSource, QStringLiteral("preferences-plugin"));
}

QTEST_GUILESS_MAIN(TestCatalogEntry)
#include "tst_catalogentry.moc"
