#include <QFile>
#include <QGuiApplication>
#include <QStandardPaths>
#include <QTemporaryDir>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "browser/session/sessionmanager.h"
#include "browser/tabs/tab.h"
#include "browser/tabs/tabmodel.h"
#include "../common/isolatedhome.h"

namespace {
void writeSessionFile(const QByteArray &content)
{
    QFile file(QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)
               + QStringLiteral("/session.json"));
    QVERIFY(file.open(QIODevice::WriteOnly));
    file.write(content);
}

QString sessionFilePath()
{
    return QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)
        + QStringLiteral("/session.json");
}
}

class TestSessionManager : public QObject
{
    Q_OBJECT

private slots:
    void init();
    void savesEveryNormalWindow();
    void keepsTheSessionWhenOnlyPrivateWindowsRemain();
    void readsTheVersionOneFormat();
    void ignoresInvalidAndFutureFiles();
    void savesNewTabPageAsAboutNewTab();

private:
    static TabModel *savedNormalWindow();
    static TabModel *privateWindow();
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

TabModel *TestSessionManager::savedNormalWindow()
{
    auto *window = new TabModel;
    window->addTab(false, QUrl(QStringLiteral("https://example.org/")));
    SessionManager::instance()->save(window);
    return window;
}

TabModel *TestSessionManager::privateWindow()
{
    auto *window = new TabModel;
    window->setPrivateTabs(true);
    window->addTab(true, QUrl(QStringLiteral("https://private.example/")));
    return window;
}

void TestSessionManager::keepsTheSessionWhenOnlyPrivateWindowsRemain()
{
    SessionManager *session = SessionManager::instance();
    TabModel *normalWindow = savedNormalWindow();
    QCOMPARE(session->savedWindows().size(), 1);
    TabModel *closingPrivateWindow = privateWindow();

    delete normalWindow;
    session->save(closingPrivateWindow);

    const QList<SessionWindow> windows = session->savedWindows();
    QCOMPARE(windows.size(), 1);
    QCOMPARE(windows.at(0).tabs.size(), 1);
    QCOMPARE(windows.at(0).tabs.at(0).url, QUrl(QStringLiteral("https://example.org/")));

    delete closingPrivateWindow;
}

void TestSessionManager::readsTheVersionOneFormat()
{
    writeSessionFile(R"({"version":1,"currentIndex":1,"tabs":[)"
                     R"({"url":"https://a.example/","title":"A"},)"
                     R"({"url":"about:newtab","title":""}]})");

    const QList<SessionWindow> windows = SessionManager::instance()->savedWindows();

    QCOMPARE(windows.size(), 1);
    QCOMPARE(windows.at(0).currentIndex, 1);
    QCOMPARE(windows.at(0).tabs.size(), 2);
    QCOMPARE(windows.at(0).tabs.at(0).title, QStringLiteral("A"));
    QVERIFY(windows.at(0).tabs.at(1).url.isEmpty());
}

void TestSessionManager::ignoresInvalidAndFutureFiles()
{
    writeSessionFile("not json");
    QVERIFY(SessionManager::instance()->savedWindows().isEmpty());

    writeSessionFile(R"({"version":3,"windows":[{"currentIndex":0,"tabs":[{"url":"https://a.example/"}]}]})");
    QVERIFY(SessionManager::instance()->savedWindows().isEmpty());

    writeSessionFile(R"({"version":2,"windows":[{"currentIndex":0,"tabs":[]}]})");
    QVERIFY(SessionManager::instance()->savedWindows().isEmpty());
}

void TestSessionManager::savesNewTabPageAsAboutNewTab()
{
    TabModel model;
    model.addTab();

    SessionManager::instance()->save(&model);

    QFile file(sessionFilePath());
    QVERIFY(file.open(QIODevice::ReadOnly));
    QVERIFY(file.readAll().contains("\"url\":\"about:newtab\""));
    QVERIFY(SessionManager::instance()->savedWindows().at(0).tabs.at(0).url.isEmpty());
}

int main(int argc, char *argv[])
{
    QStandardPaths::setTestModeEnabled(true);
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();

    QTemporaryDir home;
    if (!useIsolatedHome(home))
        return 1;

    QGuiApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE-Test"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor-SessionManager-Test"));

    TestSessionManager test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_sessionmanager.moc"
