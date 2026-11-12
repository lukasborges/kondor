#include <QCoreApplication>
#include <QTest>

#include "app/aboutinfo.h"

class TestAboutInfo : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void versionMatchesProjectVersion();
    void licenseTextIsEmbedded();
    void runtimeVersionsAreFilled();
};

void TestAboutInfo::initTestCase()
{
    QCoreApplication::setApplicationVersion(QStringLiteral(PROJECT_VERSION));
}

void TestAboutInfo::versionMatchesProjectVersion()
{
    QCOMPARE(AboutInfo::instance()->version(), QStringLiteral(PROJECT_VERSION));
}

void TestAboutInfo::licenseTextIsEmbedded()
{
    QVERIFY(AboutInfo::instance()->licenseText().startsWith(
        QStringLiteral("GNU GENERAL PUBLIC LICENSE")));
}

void TestAboutInfo::runtimeVersionsAreFilled()
{
    AboutInfo *info = AboutInfo::instance();
    QVERIFY(!info->qtRuntimeVersion().isEmpty());
    QVERIFY(!info->chromiumVersion().isEmpty());
}

QTEST_MAIN(TestAboutInfo)
#include "tst_aboutinfo.moc"
