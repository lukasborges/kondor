#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QTemporaryDir>
#include <QTest>

#include "extensions/manifestvalidator.h"

class TestManifestValidator : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void acceptsTheBaseManifest();
    void reportsTheFirstErrorWithTodaysText_data();
    void reportsTheFirstErrorWithTodaysText();

private:
    QTemporaryDir m_directory;
};

namespace {

QJsonObject baseManifest()
{
    return {{QStringLiteral("kondor"), 1},
            {QStringLiteral("id"), QStringLiteral("sample-test")},
            {QStringLiteral("name"), QStringLiteral("Sample")},
            {QStringLiteral("version"), QStringLiteral("1.0.0")}};
}

QJsonObject scriptWith(const QString &key, const QJsonValue &value)
{
    QJsonObject script{{QStringLiteral("matches"), QJsonArray{QStringLiteral("*://a/*")}},
                       {QStringLiteral("js"), QJsonArray{QStringLiteral("a.js")}}};
    script.insert(key, value);
    return script;
}

QJsonObject withScripts(const QJsonObject &script)
{
    QJsonObject manifest = baseManifest();
    manifest.insert(QStringLiteral("contentScripts"), QJsonArray{script});
    return manifest;
}

QJsonObject with(const QString &key, const QJsonValue &value)
{
    QJsonObject manifest = baseManifest();
    manifest.insert(key, value);
    return manifest;
}

QJsonObject withoutKey(const QString &key)
{
    QJsonObject manifest = baseManifest();
    manifest.remove(key);
    return manifest;
}

void addRow(const char *name, const QJsonObject &manifest, const char *error)
{
    QTest::newRow(name) << manifest << QString::fromLatin1(error);
}

}

void TestManifestValidator::initTestCase()
{
    QVERIFY(m_directory.isValid());
    QFile file(m_directory.filePath(QStringLiteral("a.js")));
    QVERIFY(file.open(QIODevice::WriteOnly));
    QVERIFY(QImage(10, 10, QImage::Format_ARGB32).save(m_directory.filePath(QStringLiteral("small.png"))));
}

void TestManifestValidator::acceptsTheBaseManifest()
{
    ManifestValidator validator(m_directory.path());
    const auto valid = validator.validate(withScripts(scriptWith(QStringLiteral("allFrames"), true)));
    QVERIFY2(valid, qPrintable(validator.error()));
    QCOMPARE(valid->contentScripts.size(), 1);
    QCOMPARE(valid->iconSource, QStringLiteral("preferences-plugin"));
}

namespace {

void addIdentityRows()
{
    addRow("no api", withoutKey(QStringLiteral("kondor")), "manifest.json: kondor: required");
    addRow("api 2", with(QStringLiteral("kondor"), 2), "manifest.json: kondor: unsupported API version (must be 1)");
    addRow("no name", withoutKey(QStringLiteral("name")), "manifest.json: name: required, must be a string");
    addRow("author", with(QStringLiteral("author"), 3), "manifest.json: author: must be a string");
    addRow("id", with(QStringLiteral("id"), QStringLiteral("A")), "manifest.json: id: must match ^[a-z0-9][a-z0-9-]{1,47}$");
    addRow("version", with(QStringLiteral("version"), QStringLiteral("1")), "manifest.json: version: must be MAJOR.MINOR.PATCH");
}

void addContentRows()
{
    addRow("permissions", with(QStringLiteral("permissions"), 1), "manifest.json: permissions: must be a list of strings");
    addRow("permission", with(QStringLiteral("permissions"), QJsonArray{QStringLiteral("root")}),
           "manifest.json: permissions: unknown permission: root");
    addRow("scripts", with(QStringLiteral("contentScripts"), 1), "manifest.json: contentScripts: must be a list");
    addRow("script", with(QStringLiteral("contentScripts"), QJsonArray{1}), "manifest.json: contentScripts[0]: must be an object");
    addRow("matches", withScripts(scriptWith(QStringLiteral("matches"), QJsonArray())),
           "manifest.json: contentScripts[0].matches: must not be empty");
    addRow("js", withScripts(scriptWith(QStringLiteral("js"), QJsonArray{QStringLiteral("b.js")})),
           "manifest.json: contentScripts[0].js: file not found: b.js");
    addRow("runAt", withScripts(scriptWith(QStringLiteral("runAt"), QStringLiteral("now"))),
           "manifest.json: contentScripts[0].runAt: must be document-start, document-end or document-idle");
}

void addSectionRows()
{
    addRow("settings", with(QStringLiteral("settings"), 1), "manifest.json: settings: must be a list");
    addRow("setting key", with(QStringLiteral("settings"), QJsonArray{QJsonObject()}),
           "manifest.json: settings[0].key: required and unique");
    addRow("action", with(QStringLiteral("action"), 1), "manifest.json: action: must be an object");
    addRow("icon", with(QStringLiteral("icon"), QStringLiteral("small.png")),
           "manifest.json: icon: a PNG icon must be at least 64 px: small.png");
}

}

void TestManifestValidator::reportsTheFirstErrorWithTodaysText_data()
{
    QTest::addColumn<QJsonObject>("manifest");
    QTest::addColumn<QString>("message");
    addIdentityRows();
    addContentRows();
    addSectionRows();
}

void TestManifestValidator::reportsTheFirstErrorWithTodaysText()
{
    QFETCH(QJsonObject, manifest);
    QFETCH(QString, message);
    ManifestValidator validator(m_directory.path());
    QVERIFY(!validator.validate(manifest));
    QCOMPARE(validator.error(), message);
}

QTEST_GUILESS_MAIN(TestManifestValidator)
#include "tst_manifestvalidator.moc"
