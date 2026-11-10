#include <QTest>
#include <QUrl>

#include "filehelper.h"

class TestFileHelper : public QObject
{
    Q_OBJECT

private slots:
    void keepsHashAndPercent();
    void keepsSpaces();
};

void TestFileHelper::keepsHashAndPercent()
{
    const QUrl url = FileHelper::instance()->suggestedFileUrl(
        QStringLiteral("/tmp/downloads"), QStringLiteral("C# 100% Guide"), QStringLiteral(".pdf"));
    QVERIFY(url.isLocalFile());
    QVERIFY(!url.hasFragment());
    QCOMPARE(url.toLocalFile(), QStringLiteral("/tmp/downloads/C# 100% Guide.pdf"));
}

void TestFileHelper::keepsSpaces()
{
    const QUrl url = FileHelper::instance()->suggestedFileUrl(
        QStringLiteral("/tmp/my downloads"), QStringLiteral("a/b"), QStringLiteral(".html"));
    QCOMPARE(url.toLocalFile(), QStringLiteral("/tmp/my downloads/a_b.html"));
}

QTEST_GUILESS_MAIN(TestFileHelper)
#include "tst_filehelper.moc"
