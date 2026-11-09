#include <QTemporaryDir>
#include <QTest>

#include "startupurl.h"

class TestStartupUrl : public QObject
{
    Q_OBJECT

private slots:
    void convertsArguments_data();
    void convertsArguments();
    void resolvesRelativeFilesAgainstWorkingDirectory();
};

void TestStartupUrl::convertsArguments_data()
{
    QTest::addColumn<QString>("argument");
    QTest::addColumn<QString>("expected");

    QTest::newRow("explicit url")
        << QStringLiteral("https://kde.org") << QStringLiteral("https://kde.org");
    QTest::newRow("naked domain")
        << QStringLiteral("kde.org") << QStringLiteral("https://kde.org");
    QTest::newRow("about scheme")
        << QStringLiteral("about:blank") << QStringLiteral("about:blank");
    QTest::newRow("free text searches")
        << QStringLiteral("some words")
        << QStringLiteral("https://duckduckgo.com/?q=some%20words");
    QTest::newRow("single word searches")
        << QStringLiteral("kde") << QStringLiteral("https://duckduckgo.com/?q=kde");
    QTest::newRow("blank arguments are ignored")
        << QStringLiteral("   ") << QString();
}

void TestStartupUrl::convertsArguments()
{
    QFETCH(QString, argument);
    QFETCH(QString, expected);

    const QUrl homePage(QStringLiteral("https://home.example/"));
    const QString searchTemplate = QStringLiteral("https://duckduckgo.com/?q=%1");

    const QUrl actual = startupUrlForArgument(argument, QStringLiteral("/tmp"),
                                              homePage, searchTemplate);
    QCOMPARE(actual.toString(QUrl::FullyEncoded), expected);
}

void TestStartupUrl::resolvesRelativeFilesAgainstWorkingDirectory()
{
    QTemporaryDir directory;
    QVERIFY(directory.isValid());

    const QString path = directory.filePath(QStringLiteral("page.html"));
    QFile file(path);
    QVERIFY(file.open(QIODevice::WriteOnly));
    file.write("<html></html>");
    file.close();

    const QUrl homePage(QStringLiteral("https://home.example/"));
    const QString searchTemplate = QStringLiteral("https://duckduckgo.com/?q=%1");
    const QString expected = QUrl::fromLocalFile(path).toString(QUrl::FullyEncoded);

    QCOMPARE(startupUrlForArgument(QStringLiteral("./page.html"), directory.path(),
                                   homePage, searchTemplate)
                 .toString(QUrl::FullyEncoded),
             expected);
    QCOMPARE(startupUrlForArgument(QStringLiteral("page.html"), directory.path(),
                                   homePage, searchTemplate)
                 .toString(QUrl::FullyEncoded),
             expected);
    QCOMPARE(startupUrlForArgument(path, directory.path(), homePage, searchTemplate)
                 .toString(QUrl::FullyEncoded),
             expected);
}

QTEST_GUILESS_MAIN(TestStartupUrl)
#include "tst_startupurl.moc"
