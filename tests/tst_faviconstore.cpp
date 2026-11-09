#include <QCoreApplication>
#include <QDateTime>
#include <QImage>
#include <QSqlQuery>
#include <QStandardPaths>
#include <QTest>

#include "database.h"
#include "faviconstore.h"
#include "historymanager.h"

class TestFaviconStore : public QObject
{
    Q_OBJECT

private slots:
    void init();
    void storesAndLooksUpByHost();
    void replacesOnlyWhenBytesChange();
    void clearHistorySinceKeepsOlderFavicons();
    void clearAllRemovesEveryFavicon();
    void clearHistoryAlsoClearsFavicons();

private:
    static QImage makeImage(const QColor &color);
};

void TestFaviconStore::init()
{
    QVERIFY(Database::instance()->isValid());
    QSqlQuery clear(Database::instance()->handle());
    QVERIFY(clear.exec(QStringLiteral("DELETE FROM favicons")));
}

QImage TestFaviconStore::makeImage(const QColor &color)
{
    QImage image(4, 4, QImage::Format_ARGB32);
    image.fill(color);
    return image;
}

void TestFaviconStore::storesAndLooksUpByHost()
{
    FaviconStore *store = FaviconStore::instance();
    store->storeImage(QStringLiteral("kde.org"), makeImage(Qt::red));

    const QImage image = store->imageForHost(QStringLiteral("kde.org"));
    QVERIFY(!image.isNull());
    QCOMPARE(image.size(), QSize(4, 4));
    QCOMPARE(image.pixelColor(0, 0), QColor(Qt::red));

    QVERIFY(store->imageForHost(QStringLiteral("example.org")).isNull());
}

void TestFaviconStore::replacesOnlyWhenBytesChange()
{
    FaviconStore *store = FaviconStore::instance();
    const QImage red = makeImage(Qt::red);
    store->storeImage(QStringLiteral("kde.org"), red);
    const int revision = store->revision();

    // The same pixels are the same PNG: no revision bump, no pointless reload.
    store->storeImage(QStringLiteral("kde.org"), red);
    QCOMPARE(store->revision(), revision);

    store->storeImage(QStringLiteral("kde.org"), makeImage(Qt::blue));
    QCOMPARE(store->revision(), revision + 1);
    QCOMPARE(store->imageForHost(QStringLiteral("kde.org")).pixelColor(0, 0),
             QColor(Qt::blue));
}

void TestFaviconStore::clearHistorySinceKeepsOlderFavicons()
{
    FaviconStore *store = FaviconStore::instance();
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    store->storeImage(QStringLiteral("recent.example"), makeImage(Qt::red));
    store->storeImage(QStringLiteral("old.example"), makeImage(Qt::blue));

    // storeImage() timestamps rows with "now"; age one of them by hand so the
    // history's "clear since" window can be checked.
    QSqlQuery age(Database::instance()->handle());
    age.prepare(QStringLiteral("UPDATE favicons SET updated_at = ? WHERE host = ?"));
    age.addBindValue(now - 100000);
    age.addBindValue(QStringLiteral("old.example"));
    QVERIFY(age.exec());

    HistoryManager::instance()->clearSince(now - 1000);

    QVERIFY(store->imageForHost(QStringLiteral("recent.example")).isNull());
    QVERIFY(!store->imageForHost(QStringLiteral("old.example")).isNull());
}

void TestFaviconStore::clearAllRemovesEveryFavicon()
{
    FaviconStore *store = FaviconStore::instance();
    store->storeImage(QStringLiteral("kde.org"), makeImage(Qt::red));
    store->storeImage(QStringLiteral("example.org"), makeImage(Qt::blue));

    store->clearAll();

    QVERIFY(store->imageForHost(QStringLiteral("kde.org")).isNull());
    QVERIFY(store->imageForHost(QStringLiteral("example.org")).isNull());
}

void TestFaviconStore::clearHistoryAlsoClearsFavicons()
{
    FaviconStore *store = FaviconStore::instance();
    store->storeImage(QStringLiteral("kde.org"), makeImage(Qt::red));
    HistoryManager::instance()->addVisit(QUrl(QStringLiteral("https://kde.org/")),
                                         QStringLiteral("KDE"));

    // Clearing history must not leave stored hosts behind: they reveal which
    // sites the user visited.
    HistoryManager::instance()->clearAll();

    QVERIFY(store->imageForHost(QStringLiteral("kde.org")).isNull());
}

int main(int argc, char *argv[])
{
    // Keep the database out of the real user directories.
    QStandardPaths::setTestModeEnabled(true);
    QCoreApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor"));

    TestFaviconStore test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_faviconstore.moc"
