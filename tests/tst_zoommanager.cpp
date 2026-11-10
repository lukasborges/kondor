#include <QSettings>
#include <QSignalSpy>
#include <QStandardPaths>
#include <QTest>

#include "zoommanager.h"

class TestZoomManager : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void hostOf();
    void saveAndReset();
    void stepLevels();
};

void TestZoomManager::initTestCase()
{
    QStandardPaths::setTestModeEnabled(true);
    QSettings settings(QStringLiteral("KDE"), QStringLiteral("Kondor"));
    settings.clear();
    settings.sync();
}

void TestZoomManager::hostOf()
{
    auto *zoom = ZoomManager::instance();
    QCOMPARE(zoom->hostOf(QUrl(QStringLiteral("https://KDE.org/a?b"))), QStringLiteral("kde.org"));
    QCOMPARE(zoom->hostOf(QUrl(QStringLiteral("about:blank"))), QString());
    QCOMPARE(zoom->hostOf(QUrl(QStringLiteral("file:///tmp/a.html"))), QString());
}

void TestZoomManager::saveAndReset()
{
    auto *zoom = ZoomManager::instance();
    QSignalSpy spy(zoom, &ZoomManager::zoomChanged);
    QCOMPARE(zoom->zoomFor(QStringLiteral("kde.org")), 1.0);
    zoom->setZoomFor(QStringLiteral("kde.org"), 1.25);
    QCOMPARE(zoom->zoomFor(QStringLiteral("kde.org")), 1.25);
    QCOMPARE(zoom->zoomFor(QStringLiteral("example.com")), 1.0);
    QCOMPARE(spy.count(), 1);

    // Stored on disk, and removed again at 100%.
    QSettings settings(QStringLiteral("KDE"), QStringLiteral("Kondor"));
    QVERIFY(settings.contains(QStringLiteral("SiteZoom/kde.org")));
    zoom->setZoomFor(QStringLiteral("kde.org"), 1.25);
    QCOMPARE(spy.count(), 1);
    zoom->setZoomFor(QStringLiteral("kde.org"), 1.0);
    settings.sync();
    QVERIFY(!settings.contains(QStringLiteral("SiteZoom/kde.org")));
    QCOMPARE(spy.count(), 2);
}

void TestZoomManager::stepLevels()
{
    auto *zoom = ZoomManager::instance();
    QCOMPARE(zoom->step(1.0, 1), 1.1);
    QCOMPARE(zoom->step(1.1, 1), 1.25);
    QCOMPARE(zoom->step(1.0, -1), 0.9);
    QCOMPARE(zoom->step(5.0, 1), 5.0);
    QCOMPARE(zoom->step(0.3, -1), 0.3);
    // Between levels (e.g. after Ctrl+wheel).
    QCOMPARE(zoom->step(1.2, 1), 1.25);
    QCOMPARE(zoom->step(1.2, -1), 1.1);
}

QTEST_GUILESS_MAIN(TestZoomManager)
#include "tst_zoommanager.moc"
