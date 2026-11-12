#include "extensionsharness.h"

class TestExtensionPackage : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void validSample();
    void invalidFixtures_data();
    void invalidFixtures();
    void tooManyFiles();
    void tooLargePackage();
    void tooLargeArchive();
    void unsafeArchiveEntry();
    void localizedStrings();
    void permissionLinesForSites();
    void permissionLinesForCapabilities();

private:
    QTemporaryDir m_work;
};

void TestExtensionPackage::initTestCase()
{
    QVERIFY(m_work.isValid());
}

void TestExtensionPackage::validSample()
{
    QString error;
    const ExtensionPackage package = ExtensionPackage::load(dataDir(QStringLiteral("sample")), &error);
    QVERIFY2(package.isValid(), qPrintable(error));
    QCOMPARE(package.id(), QStringLiteral("sample"));
    QCOMPARE(package.version(), QStringLiteral("1.0.0"));
    QCOMPARE(package.permissions(), (QStringList{QStringLiteral("tabs"), QStringLiteral("notifications")}));
    QCOMPARE(package.contentScripts().size(), 1);
    QCOMPARE(package.contentScripts().first().runAt, QStringLiteral("document-end"));
    QVERIFY(package.hasSettings());
    QVERIFY(package.hasAction());
    QVERIFY(package.actionSiteToggle());
    QVERIFY(package.iconSource().startsWith(QLatin1String("file://")));
    QCOMPARE(package.settingDefaults().value(QStringLiteral("greeting")).toString(),
             QStringLiteral("hello"));
}

void TestExtensionPackage::invalidFixtures_data()
{
    QTest::addColumn<QString>("fixture");
    QTest::addColumn<QString>("message");
    QTest::newRow("missing file") << QStringLiteral("missing-file")
        << QStringLiteral("manifest.json: contentScripts[0].js: file not found: content.js");
    QTest::newRow("bad id") << QStringLiteral("bad-id")
        << QStringLiteral("manifest.json: id: must match ^[a-z0-9][a-z0-9-]{1,47}$");
    QTest::newRow("dot dot") << QStringLiteral("dotdot")
        << QStringLiteral("manifest.json: contentScripts[0].js: invalid path: ../secret.js");
    QTest::newRow("no manifest") << QStringLiteral("does-not-exist")
        << QStringLiteral("manifest.json: file not found");
}

void TestExtensionPackage::invalidFixtures()
{
    QFETCH(QString, fixture);
    QFETCH(QString, message);
    QString error;
    const ExtensionPackage package = ExtensionPackage::load(dataDir(fixture), &error);
    QVERIFY(!package.isValid());
    QCOMPARE(error, message);
}

void TestExtensionPackage::tooManyFiles()
{
    const QString dir = makeVariant(m_work.path(), QStringLiteral("many"), [](QJsonObject &) {});
    for (int i = 0; i < ExtensionPackage::kMaxPackageFiles; ++i)
        QVERIFY(writeFile(dir + QStringLiteral("/extra/f%1.txt").arg(i), "x"));
    QString error;
    QVERIFY(!ExtensionPackage::load(dir, &error).isValid());
    QVERIFY2(error.contains(QLatin1String("200 files")), qPrintable(error));
}

void TestExtensionPackage::tooLargePackage()
{
    const QString dir = makeVariant(m_work.path(), QStringLiteral("large"), [](QJsonObject &) {});
    QVERIFY(writeFile(dir + QStringLiteral("/big.bin"),
                      QByteArray(int(ExtensionPackage::kMaxPackageBytes) + 1, 'x')));
    QString error;
    QVERIFY(!ExtensionPackage::load(dir, &error).isValid());
    QVERIFY2(error.contains(QLatin1String("larger than 5 MiB")), qPrintable(error));
}

void TestExtensionPackage::tooLargeArchive()
{
    const QString dir = makeVariant(m_work.path(), QStringLiteral("largezip"), [](QJsonObject &) {});
    QVERIFY(writeFile(dir + QStringLiteral("/big.bin"),
                      QByteArray(int(ExtensionPackage::kMaxPackageBytes) + 1, 'x')));
    const QString zip = m_work.path() + QStringLiteral("/large.kondorext");
    QVERIFY(zipDirectory(dir, zip));
    QString error;
    QVERIFY(!ExtensionPackage::unpack(zip, m_work.path() + QStringLiteral("/unpacked-large"), &error));
    QVERIFY2(error.contains(QLatin1String("larger than 5 MiB")), qPrintable(error));
    QVERIFY(!QFileInfo::exists(m_work.path() + QStringLiteral("/unpacked-large/big.bin")));
}

void TestExtensionPackage::unsafeArchiveEntry()
{
    const QString zipPath = m_work.path() + QStringLiteral("/unsafe.kondorext");
    QFile::remove(zipPath);
    {
        KZip zip(zipPath);
        QVERIFY(zip.open(QIODevice::WriteOnly));
        QVERIFY(zip.writeFile(QStringLiteral("manifest.json"), QByteArray("{}")));
        QVERIFY(zip.writeFile(QStringLiteral("../evil.js"), QByteArray("x")));
        QVERIFY(zip.close());
    }
    QString error;
    const QString target = m_work.path() + QStringLiteral("/unpacked-unsafe");
    QVERIFY(!ExtensionPackage::unpack(zipPath, target, &error));
    QVERIFY2(error.contains(QLatin1String("Unsafe file name")), qPrintable(error));
    QVERIFY(!QFileInfo::exists(m_work.path() + QStringLiteral("/evil.js")));
}

void TestExtensionPackage::localizedStrings()
{
    const ExtensionPackage package = ExtensionPackage::load(dataDir(QStringLiteral("sample")));
    QCOMPARE(package.name(QStringLiteral("pt_BR")), QStringLiteral("Extensão de Exemplo"));
    QCOMPARE(package.name(QStringLiteral("pt_PT")), QStringLiteral("Sample Extension"));
    QCOMPARE(package.name(QStringLiteral("de")), QStringLiteral("Sample Extension"));
    const QVariantList settings = package.settingsSchema(QStringLiteral("pt_BR"));
    QCOMPARE(settings.first().toMap().value(QStringLiteral("label")).toString(), QStringLiteral("Saudação"));
    QCOMPARE(package.actionItems(QStringLiteral("pt_BR")).first().toMap().value(QStringLiteral("title")).toString(),
             QStringLiteral("Alternar Marca"));
}

void TestExtensionPackage::permissionLinesForSites()
{
    const QStringList all{QStringLiteral("https://*/*"), QStringLiteral("http://*/*")};
    QCOMPARE(ExtensionPackage::permissionLines(all, {}),
             (QStringList{QStringLiteral("Read and change all websites")}));
    QCOMPARE(ExtensionPackage::permissionLines({QStringLiteral("<all_urls>")}, {}).size(), 1);

    QCOMPARE(ExtensionPackage::permissionLines({QStringLiteral("*://www.youtube.com/*")}, {}),
             (QStringList{QStringLiteral("Read and change pages on www.youtube.com")}));

    const QStringList many{QStringLiteral("https://a.com/*"), QStringLiteral("https://b.com/*"),
                           QStringLiteral("https://c.com/*"), QStringLiteral("https://d.com/*"),
                           QStringLiteral("https://e.com/*")};
    QCOMPARE(ExtensionPackage::permissionLines(many, {}).first(),
             QStringLiteral("Read and change pages on a.com, b.com, c.com and 2 more"));
}

void TestExtensionPackage::permissionLinesForCapabilities()
{
    const QStringList lines = ExtensionPackage::permissionLines(
        {QStringLiteral("<all_urls>")},
        {QStringLiteral("tabs"), QStringLiteral("downloads"), QStringLiteral("notifications")});
    QCOMPARE(lines.size(), 4);
    QCOMPARE(lines.at(1), QStringLiteral("Open, close and navigate your tabs"));
    QCOMPARE(lines.at(2), QStringLiteral("Download files"));
    QCOMPARE(lines.at(3), QStringLiteral("Show notifications"));
}

int runTestExtensionPackage(int argc, char *argv[])
{
    TestExtensionPackage test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensionpackage.moc"
