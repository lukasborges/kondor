#include <QTest>

#include "app/extensionpackages.h"

class TestExtensionPackages : public QObject
{
    Q_OBJECT

private slots:
    void takesLocalPackagesOutOfTheUrls();
    void keepsRemoteUrlsThatLookLikePackages();
};

void TestExtensionPackages::takesLocalPackagesOutOfTheUrls()
{
    QList<QUrl> urls = {QUrl::fromLocalFile(QStringLiteral("/tmp/a.kondorext")),
                        QUrl(QStringLiteral("https://kde.org")),
                        QUrl::fromLocalFile(QStringLiteral("/tmp/B.KONDOREXT"))};

    const QStringList packages = takeExtensionPackages(urls);

    QCOMPARE(packages, QStringList({QStringLiteral("/tmp/a.kondorext"),
                                    QStringLiteral("/tmp/B.KONDOREXT")}));
    QCOMPARE(urls, QList<QUrl>{QUrl(QStringLiteral("https://kde.org"))});
}

void TestExtensionPackages::keepsRemoteUrlsThatLookLikePackages()
{
    QList<QUrl> urls = {QUrl(QStringLiteral("https://example.com/a.kondorext"))};

    QVERIFY(takeExtensionPackages(urls).isEmpty());
    QCOMPARE(urls.size(), 1);
}

QTEST_GUILESS_MAIN(TestExtensionPackages)
#include "tst_extensionpackages.moc"
