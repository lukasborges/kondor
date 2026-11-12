#include <QGuiApplication>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickStyle>
#include <QTemporaryDir>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "downloads/downloadmanager.h"

namespace {
const qint64 kMegabyte = 1000 * 1000;

struct Case
{
    const char *name;
    int state;
    bool isPaused;
    qint64 received;
    qint64 total;
    const char *speed;
    const char *reason;
    const char *text;
};

const Case kCases[] = {
    { "requested", DownloadManager::Requested, false, 0, 0, "", "",
      "Waiting for confirmation…" },
    { "progressWithTotalAndSpeed", DownloadManager::InProgress, false, kMegabyte,
      4 * kMegabyte, "1 MB/s", "", "%R of %T — 1 MB/s" },
    { "progressWithTotal", DownloadManager::InProgress, false, kMegabyte, 4 * kMegabyte, "", "",
      "%R of %T" },
    { "progressWithSpeed", DownloadManager::InProgress, false, kMegabyte, 0, "1 MB/s", "",
      "%R downloaded — 1 MB/s" },
    { "progressWithoutTotalOrSpeed", DownloadManager::InProgress, false, kMegabyte, 0, "", "",
      "%R downloaded" },
    { "pausedWithTotal", DownloadManager::InProgress, true, kMegabyte, 4 * kMegabyte, "", "",
      "Paused — %R of %T" },
    { "pausedWithoutTotal", DownloadManager::InProgress, true, kMegabyte, 0, "", "",
      "Paused — %R" },
    { "completed", DownloadManager::Completed, false, kMegabyte, kMegabyte, "", "",
      "Completed — %R" },
    { "canceled", DownloadManager::Cancelled, false, 0, 0, "", "", "Canceled" },
    { "failedWithReason", DownloadManager::Interrupted, false, 0, 0, "", "Network failed",
      "Failed — Network failed" },
    { "failedWithoutReason", DownloadManager::Interrupted, false, 0, 0, "", "", "Failed" }
};

QString expectedText(const char *pattern)
{
    return QString::fromUtf8(pattern)
            .replace(QLatin1String("%R"), QLocale().formattedDataSize(kMegabyte))
            .replace(QLatin1String("%T"), QLocale().formattedDataSize(4 * kMegabyte));
}
}

class TestDownloadStatus : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void describesEveryState_data();
    void describesEveryState();

private:
    QQmlEngine m_engine;
    QObject *m_status = nullptr;
};

void TestDownloadStatus::initTestCase()
{
    qmlRegisterSingletonType<DownloadManager>("Kondor", 1, 0, "DownloadManager",
                                              [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                  return DownloadManager::instance();
                                              });
    m_engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));
    QQmlComponent component(&m_engine,
                            QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR
                                                               "/downloads/DownloadStatus.qml")));
    m_status = component.create();
    if (!m_status)
        qWarning() << component.errors();
    QVERIFY(m_status);
}

void TestDownloadStatus::describesEveryState_data()
{
    QTest::addColumn<int>("state");
    QTest::addColumn<bool>("isPaused");
    QTest::addColumn<qint64>("received");
    QTest::addColumn<qint64>("total");
    QTest::addColumn<QString>("speed");
    QTest::addColumn<QString>("reason");
    QTest::addColumn<QString>("expected");

    for (const Case &row : kCases)
        QTest::newRow(row.name) << row.state << row.isPaused << row.received << row.total
                                << QString::fromLatin1(row.speed) << QString::fromLatin1(row.reason)
                                << expectedText(row.text);
}

void TestDownloadStatus::describesEveryState()
{
    QFETCH(int, state);
    QFETCH(bool, isPaused);
    QFETCH(qint64, received);
    QFETCH(qint64, total);
    QFETCH(QString, speed);
    QFETCH(QString, reason);
    QFETCH(QString, expected);

    const QVariantMap download{ { QStringLiteral("state"), state },
                                { QStringLiteral("isPaused"), isPaused },
                                { QStringLiteral("receivedBytes"), received },
                                { QStringLiteral("totalBytes"), total },
                                { QStringLiteral("speedText"), speed },
                                { QStringLiteral("interruptReasonString"), reason } };
    QVariant text;
    QMetaObject::invokeMethod(m_status, "text", Q_RETURN_ARG(QVariant, text),
                              Q_ARG(QVariant, download));
    QCOMPARE(text.toString(), expected);
}

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();

    QTemporaryDir home;
    if (!home.isValid())
        return 1;
    qputenv("XDG_DATA_HOME", home.path().toUtf8());
    qputenv("XDG_CONFIG_HOME", home.path().toUtf8());
    qputenv("XDG_CACHE_HOME", home.path().toUtf8());

    QGuiApplication app(argc, argv);
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));

    TestDownloadStatus test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_downloadstatus.moc"
