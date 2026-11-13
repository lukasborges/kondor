#include <QJsonArray>
#include <QJsonObject>
#include <QStandardPaths>
#include <QTest>

#include "core/database.h"
#include "extensions/extensionstorage.h"

class TestExtensionStorage : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void init();
    void valuesKeepTheirJsonType();
    void quotaCountsTheOtherKeysOnly();
    void removeExtensionKeepsOtherExtensions();
};

namespace {

QJsonValue bigText(int kibibytes, QChar letter)
{
    return QJsonValue(QString(kibibytes * 1024, letter));
}

}

void TestExtensionStorage::initTestCase()
{
    QStandardPaths::setTestModeEnabled(true);
    QVERIFY(Database::instance()->isValid());
}

void TestExtensionStorage::init()
{
    ExtensionStorage::removeExtension(QStringLiteral("one"));
    ExtensionStorage::removeExtension(QStringLiteral("two"));
}

void TestExtensionStorage::valuesKeepTheirJsonType()
{
    const QString id = QStringLiteral("one");
    const QJsonObject object{{QStringLiteral("n"), 1}, {QStringLiteral("list"), QJsonArray{1, 2}}};
    const QList<QJsonValue> values{QJsonValue(1.5), QJsonValue(QStringLiteral("text")), QJsonValue(true), object,
                                   QJsonValue(QJsonArray{QStringLiteral("a")})};
    for (const QJsonValue &value : values) {
        QVERIFY(ExtensionStorage::setValue(id, QStringLiteral("k"), value).isWritten);
        QCOMPARE(ExtensionStorage::value(id, QStringLiteral("k")), value);
    }
    QVERIFY(ExtensionStorage::value(id, QStringLiteral("missing")).isNull());
}

void TestExtensionStorage::quotaCountsTheOtherKeysOnly()
{
    const QString id = QStringLiteral("one");
    QVERIFY(ExtensionStorage::setValue(id, QStringLiteral("a"), bigText(600, QLatin1Char('x'))).isWritten);
    const auto refused = ExtensionStorage::setValue(id, QStringLiteral("b"), bigText(600, QLatin1Char('y')));
    QVERIFY(!refused.isWritten);
    QVERIFY(refused.error.contains(QLatin1String("full")));
    QVERIFY(ExtensionStorage::setValue(id, QStringLiteral("a"), bigText(900, QLatin1Char('z'))).isWritten);
    QCOMPARE(ExtensionStorage::keys(id), QStringList{QStringLiteral("a")});
}

void TestExtensionStorage::removeExtensionKeepsOtherExtensions()
{
    QVERIFY(ExtensionStorage::setValue(QStringLiteral("one"), QStringLiteral("k"), QJsonValue(1)).isWritten);
    QVERIFY(ExtensionStorage::setValue(QStringLiteral("two"), QStringLiteral("k"), QJsonValue(2)).isWritten);
    ExtensionStorage::removeExtension(QStringLiteral("one"));
    QVERIFY(ExtensionStorage::keys(QStringLiteral("one")).isEmpty());
    QCOMPARE(ExtensionStorage::value(QStringLiteral("two"), QStringLiteral("k")).toInt(), 2);
}

QTEST_GUILESS_MAIN(TestExtensionStorage)
#include "tst_extensionstorage.moc"
