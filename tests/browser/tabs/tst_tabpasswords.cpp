#include <QClipboard>
#include <QGuiApplication>
#include <QSignalSpy>
#include <QStandardPaths>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "browser/tabs/tab.h"
#include "browser/tabs/tabmodel.h"
#include "core/settings/settings.h"

class TestTabPasswords : public QObject
{
    Q_OBJECT

private slots:
    void init();
    void privateTabNeverOffersToSave();
    void neverSaveAddsTheOriginOnce();
    void walletNoticeReplacesTheSavePrompt();
    void dismissClearsThePrompt();
    void privateTabDoesNotCopy();
    void hostFollowsUrl();
};

void TestTabPasswords::init()
{
    Settings::instance()->setPasswordNeverSaveSites({});
}

void TestTabPasswords::privateTabNeverOffersToSave()
{
    TabModel model;
    Tab *tab = model.addTab(true);

    tab->passwords()->offerSave(QStringLiteral("https://a.example"), QStringLiteral("ann"),
                           QStringLiteral("secret"));
    tab->passwords()->showWalletNotice();

    QCOMPARE(tab->passwords()->prompt(), QString());
}

void TestTabPasswords::neverSaveAddsTheOriginOnce()
{
    TabModel model;
    Tab *tab = model.addTab();
    const QString origin = QStringLiteral("https://a.example");

    tab->passwords()->offerSave(origin, QStringLiteral("ann"), QStringLiteral("secret"));
    tab->passwords()->neverSavePending();
    tab->passwords()->offerSave(origin, QStringLiteral("ann"), QStringLiteral("secret"));
    tab->passwords()->neverSavePending();

    QCOMPARE(Settings::instance()->passwordNeverSaveSites(), QStringList{origin});
    QCOMPARE(tab->passwords()->prompt(), QString());
}

void TestTabPasswords::walletNoticeReplacesTheSavePrompt()
{
    TabModel model;
    Tab *tab = model.addTab();
    tab->passwords()->offerSave(QStringLiteral("https://a.example"), QStringLiteral("ann"),
                           QStringLiteral("secret"));
    QCOMPARE(tab->passwords()->prompt(), QStringLiteral("save"));
    QCOMPARE(tab->passwords()->promptHost(), QStringLiteral("a.example"));

    tab->passwords()->showWalletNotice();

    QCOMPARE(tab->passwords()->prompt(), QStringLiteral("walletUnavailable"));
    QCOMPARE(tab->passwords()->promptUsername(), QString());
}

void TestTabPasswords::dismissClearsThePrompt()
{
    TabModel model;
    Tab *tab = model.addTab();
    tab->passwords()->offerSave(QStringLiteral("https://a.example"), QStringLiteral("ann"),
                           QStringLiteral("secret"));
    QSignalSpy spy(tab->passwords(), &TabPasswords::promptChanged);

    tab->passwords()->dismissPrompt();

    QCOMPARE(tab->passwords()->prompt(), QString());
    QCOMPARE(tab->passwords()->promptUsername(), QString());
    QCOMPARE(spy.count(), 1);
}

void TestTabPasswords::privateTabDoesNotCopy()
{
    TabModel model;
    Tab *tab = model.addTab(true);
    QGuiApplication::clipboard()->setText(QStringLiteral("before"));

    tab->passwords()->copyUsername(QStringLiteral("ann"));
    tab->passwords()->copyPassword(QStringLiteral("ann"));

    QCOMPARE(QGuiApplication::clipboard()->text(), QStringLiteral("before"));
}

void TestTabPasswords::hostFollowsUrl()
{
    TabModel model;
    Tab *tab = model.addTab();

    tab->passwords()->updateUsernamesFor(QUrl(QStringLiteral("https://Example.org/login?x=1")));

    QCOMPARE(tab->passwords()->host(), QStringLiteral("example.org"));
}

int main(int argc, char *argv[])
{
    QStandardPaths::setTestModeEnabled(true);
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();

    QGuiApplication app(argc, argv);
    TestTabPasswords test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_tabpasswords.moc"
