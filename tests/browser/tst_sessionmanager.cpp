#include <QFile>
#include <QGuiApplication>
#include <QStandardPaths>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "browser/sessionmanager.h"
#include "browser/tab.h"
#include "browser/tabmodel.h"

namespace {
QString sessionFilePath()
{
    return QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)
        + QStringLiteral("/session.json");
}
} // namespace

class TestSessionManager : public QObject
{
    Q_OBJECT

private slots:
    void init();
    void savesEveryNormalWindow();
    void keepsTheSessionWhenOnlyPrivateWindowsRemain();
};

void TestSessionManager::init()
{
    QFile::remove(sessionFilePath());
}

void TestSessionManager::savesEveryNormalWindow()
{
    TabModel first;
    first.addTab(false, QUrl(QStringLiteral("https://one.example/")));
    TabModel second;
    second.addTab(false, QUrl(QStringLiteral("https://two.example/")));
    second.addTab(false, QUrl(QStringLiteral("https://three.example/")));

    SessionManager *session = SessionManager::instance();
    session->save(&first);
    session->save(&second);

    const QList<SessionWindow> windows = session->savedWindows();
    QCOMPARE(windows.size(), 2);
    QCOMPARE(windows.at(0).tabs.size(), 1);
    QCOMPARE(windows.at(0).tabs.at(0).url, QUrl(QStringLiteral("https://one.example/")));
    QCOMPARE(windows.at(1).tabs.size(), 2);
    QCOMPARE(windows.at(1).currentIndex, 1);
    QCOMPARE(windows.at(1).tabs.at(1).url, QUrl(QStringLiteral("https://three.example/")));
}

void TestSessionManager::keepsTheSessionWhenOnlyPrivateWindowsRemain()
{
    auto *normalWindow = new TabModel;
    normalWindow->addTab(false, QUrl(QStringLiteral("https://example.org/")));

    SessionManager *session = SessionManager::instance();
    session->save(normalWindow);
    QCOMPARE(session->savedWindows().size(), 1);

    auto *privateWindow = new TabModel;
    privateWindow->setPrivateTabs(true);
    privateWindow->addTab(true, QUrl(QStringLiteral("https://private.example/")));

    // The normal window closes, then the private one. The private window never
    // restores, so the session saved when the normal window closed must stay.
    delete normalWindow;
    session->save(privateWindow);

    const QList<SessionWindow> windows = session->savedWindows();
    QCOMPARE(windows.size(), 1);
    QCOMPARE(windows.at(0).tabs.size(), 1);
    QCOMPARE(windows.at(0).tabs.at(0).url, QUrl(QStringLiteral("https://example.org/")));

    delete privateWindow;
}

int main(int argc, char *argv[])
{
    // Keep the session file out of the real user directories.
    QStandardPaths::setTestModeEnabled(true);
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();

    QGuiApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE-Test"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor-SessionManager-Test"));

    TestSessionManager test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_sessionmanager.moc"
