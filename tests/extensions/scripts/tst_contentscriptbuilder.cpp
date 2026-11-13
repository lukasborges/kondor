#include <QFile>
#include <QTemporaryDir>
#include <QTest>

#include "extensions/scripts/contentscriptbuilder.h"

class TestContentScriptBuilder : public QObject
{
    Q_OBJECT

private slots:
    void sourceMatchesTheRecordedScript();
    void cssOnlyScriptHasNoJavaScriptBlock();
};

namespace {

void writeFile(const QString &path, const QByteArray &content)
{
    QFile file(path);
    QVERIFY(file.open(QIODevice::WriteOnly));
    file.write(content);
}

ContentScriptContext contextOf(const ExtensionPackage &package)
{
    return {&package, 0, QStringLiteral("@TOKEN@"), QStringLiteral("en"), true,
            package.settingDefaults(), {QStringLiteral("https://example.com")}};
}

}

void TestContentScriptBuilder::sourceMatchesTheRecordedScript()
{
    const QString data = QStringLiteral(KONDOR_TEST_DATA_DIR "/extensions/");
    const ExtensionPackage package = ExtensionPackage::load(data + QStringLiteral("sample"));
    QVERIFY(package.isValid());
    QFile recorded(data + QStringLiteral("sample-content-script.js"));
    QVERIFY(recorded.open(QIODevice::ReadOnly));
    QCOMPARE(contentScriptSource(contextOf(package)), QString::fromUtf8(recorded.readAll()));
}

void TestContentScriptBuilder::cssOnlyScriptHasNoJavaScriptBlock()
{
    QTemporaryDir directory;
    QVERIFY(directory.isValid());
    writeFile(directory.filePath(QStringLiteral("style.css")), "body { color: red; }");
    writeFile(directory.filePath(QStringLiteral("manifest.json")),
              R"({"kondor":1,"id":"css-only","name":"Css","version":"1.0.0",
                  "contentScripts":[{"matches":["*://a/*"],"css":["style.css"]}]})");
    const ExtensionPackage package = ExtensionPackage::load(directory.path());
    QVERIFY(package.isValid());
    const QString source = contentScriptSource(contextOf(package));
    QVERIFY(source.contains(QLatin1String("body { color: red; }")));
    QVERIFY(!source.contains(QLatin1String("(function (kondor) {")));
}

QTEST_GUILESS_MAIN(TestContentScriptBuilder)
#include "tst_contentscriptbuilder.moc"
