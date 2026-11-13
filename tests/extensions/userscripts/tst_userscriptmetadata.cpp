#include <QFile>
#include <QTest>

#include "extensions/userscripts/userscriptmetadata.h"
#include "extensions/userscripts/userscriptversion.h"

namespace {

QString fixture(const char *name)
{
    QFile file(QStringLiteral(KONDOR_TEST_DATA_DIR "/userscripts/") + QLatin1String(name));
    return file.open(QIODevice::ReadOnly) ? QString::fromUtf8(file.readAll()) : QString();
}

UserScriptMetadata parsed(const QString &source)
{
    QString error;
    const auto metadata = parseUserScriptMetadata(source, error);
    return metadata.value_or(UserScriptMetadata());
}

QString scriptWith(const QString &line)
{
    return QStringLiteral("// ==UserScript==\n// @name N\n// @match *://*/*\n%1\n// ==/UserScript==\n")
        .arg(line);
}

}

class TestUserScriptMetadata : public QObject
{
    Q_OBJECT

private slots:
    void readsEveryKey();
    void mapsRunAt_data();
    void mapsRunAt();
    void refusesInvalidScripts_data();
    void refusesInvalidScripts();
    void listsUnsupportedFeaturesInFileOrder();
    void takesTheFirstHomepageKey();
    void normalizesVersions_data();
    void normalizesVersions();
    void comparesVersions_data();
    void comparesVersions();
};

void TestUserScriptMetadata::readsEveryKey()
{
    const UserScriptMetadata metadata = parsed(fixture("wide.user.js"));
    QCOMPARE(metadata.name, QStringLiteral("Wide Test"));
    QCOMPARE(metadata.namespaceName, QStringLiteral("test"));
    QCOMPARE(metadata.version, QStringLiteral("1.0"));
    QCOMPARE(metadata.author, QStringLiteral("Jane Example"));
    QCOMPARE(metadata.homepage, QStringLiteral("https://example.org/wide"));
    QCOMPARE(metadata.license, QStringLiteral("MIT"));
    QCOMPARE(metadata.matches, QStringList{QStringLiteral("*://127.0.0.1/*")});
    QCOMPARE(metadata.includes, QStringList{QStringLiteral("https://*.example.org/*")});
    QCOMPARE(metadata.excludes, QStringList{QStringLiteral("*://127.0.0.1/excluded/*")});
    QCOMPARE(metadata.requiredUrls, QStringList{QStringLiteral("lib.js")});
    QCOMPARE(metadata.updateUrl, QStringLiteral("https://example.org/wide.meta.js"));
    QCOMPARE(metadata.downloadUrl, QStringLiteral("https://example.org/wide.user.js"));
    QVERIFY(!metadata.allFrames);
    QVERIFY(metadata.wantsNotifications());
}

void TestUserScriptMetadata::mapsRunAt_data()
{
    QTest::addColumn<QString>("line");
    QTest::addColumn<QString>("expected");
    QTest::newRow("start") << "// @run-at document-start" << "document-start";
    QTest::newRow("end") << "// @run-at document-end" << "document-end";
    QTest::newRow("body") << "// @run-at document-body" << "document-end";
    QTest::newRow("idle") << "// @run-at document-idle" << "document-idle";
    QTest::newRow("unknown") << "// @run-at context-menu" << "document-idle";
    QTest::newRow("absent") << "" << "document-idle";
}

void TestUserScriptMetadata::mapsRunAt()
{
    QFETCH(QString, line);
    QFETCH(QString, expected);
    QCOMPARE(parsed(scriptWith(line)).runAt, expected);
}

void TestUserScriptMetadata::refusesInvalidScripts_data()
{
    QTest::addColumn<QString>("file");
    QTest::newRow("no block") << "no-block.user.js";
    QTest::newRow("no name") << "no-name.user.js";
    QTest::newRow("no match") << "no-match.user.js";
}

void TestUserScriptMetadata::refusesInvalidScripts()
{
    QFETCH(QString, file);
    QString error;
    const QString source = fixture(file.toUtf8().constData());
    QVERIFY(!source.isEmpty());
    QVERIFY(!parseUserScriptMetadata(source, error));
    QVERIFY(!error.isEmpty());
}

void TestUserScriptMetadata::listsUnsupportedFeaturesInFileOrder()
{
    const UserScriptMetadata metadata = parsed(fixture("wide.user.js"));
    QCOMPARE(metadata.unsupportedFeatures(),
             (QStringList{QStringLiteral("GM_xmlhttpRequest"), QStringLiteral("@resource")}));
}

void TestUserScriptMetadata::takesTheFirstHomepageKey()
{
    const QString source = scriptWith(QStringLiteral("// @website https://a.example\n// @homepage https://b.example"));
    QCOMPARE(parsed(source).homepage, QStringLiteral("https://a.example"));
}

void TestUserScriptMetadata::normalizesVersions_data()
{
    QTest::addColumn<QString>("raw");
    QTest::addColumn<QString>("expected");
    QTest::newRow("two parts") << "1.2" << "1.2.0";
    QTest::newRow("suffix") << "0.3.1b" << "0.3.1";
    QTest::newRow("four parts") << "2024.05.01.2" << "2024.5.1";
    QTest::newRow("absent") << "" << "0.0.0";
    QTest::newRow("text") << "beta" << "0.0.0";
}

void TestUserScriptMetadata::normalizesVersions()
{
    QFETCH(QString, raw);
    QFETCH(QString, expected);
    QCOMPARE(normalizedUserScriptVersion(raw), expected);
}

void TestUserScriptMetadata::comparesVersions_data()
{
    QTest::addColumn<QString>("candidate");
    QTest::addColumn<QString>("installed");
    QTest::addColumn<bool>("isNewer");
    QTest::newRow("greater") << "1.10" << "1.9" << true;
    QTest::newRow("equal") << "1.2" << "1.2.0" << false;
    QTest::newRow("older") << "1.1" << "1.2" << false;
    QTest::newRow("longer") << "1.2.0.1" << "1.2" << true;
    QTest::newRow("suffix") << "1.0b" << "1.0" << true;
}

void TestUserScriptMetadata::comparesVersions()
{
    QFETCH(QString, candidate);
    QFETCH(QString, installed);
    QFETCH(bool, isNewer);
    QCOMPARE(isNewerUserScriptVersion(candidate, installed), isNewer);
}

QTEST_APPLESS_MAIN(TestUserScriptMetadata)

#include "tst_userscriptmetadata.moc"
