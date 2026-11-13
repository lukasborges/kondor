#include <QGuiApplication>
#include <QSignalSpy>
#include <QStandardPaths>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "browser/profile/profilemanager.h"
#include "browser/tabs/tab.h"
#include "browser/tabs/tabmodel.h"

namespace {
Tab *acceptedErrorTab(TabModel &model, const QUrl &failedUrl)
{
    Tab *tab = model.addTab();
    tab->security()->setPendingCertificateError(failedUrl, QStringLiteral("Expired"), true);
    tab->security()->acceptCertificateError();
    return tab;
}
}

class TestTabSecurity : public QObject
{
    Q_OBJECT

private slots:
    void securityStateFollowsScheme();
    void acceptingTheErrorClearsItAndAnswersTheView();
    void overrideKeepsTheErrorStateWhenComingBack();
    void overrideReachesEveryTabOfTheSameProfile();
    void privateTabNeverInheritsTheOverride();
    void rejectCertificateErrorClearsThePendingError();
};

void TestTabSecurity::securityStateFollowsScheme()
{
    TabModel model;
    Tab *tab = model.addTab();

    tab->setUrl(QUrl(QStringLiteral("https://example.com/")));
    QCOMPARE(tab->security()->state(), QStringLiteral("secure"));

    tab->setUrl(QUrl(QStringLiteral("http://example.com/")));
    QCOMPARE(tab->security()->state(), QStringLiteral("insecure"));

    tab->setUrl(QUrl(QStringLiteral("file:///etc/hosts")));
    QCOMPARE(tab->security()->state(), QStringLiteral("local"));

    tab->setUrl(QUrl(QStringLiteral("about:blank")));
    QCOMPARE(tab->security()->state(), QStringLiteral("local"));
}

void TestTabSecurity::acceptingTheErrorClearsItAndAnswersTheView()
{
    TabModel model;
    Tab *tab = model.addTab();
    QSignalSpy acceptSpy(tab->security(), &TabSecurity::acceptCertificateErrorRequested);
    tab->security()->setPendingCertificateError(QUrl(QStringLiteral("https://expired.example/")),
                                                QStringLiteral("Expired"), true);
    QVERIFY(tab->security()->certificateErrorPending());
    QCOMPARE(tab->security()->certificateErrorOverridable(), true);
    QCOMPARE(tab->security()->state(), QStringLiteral("error"));

    tab->security()->acceptCertificateError();

    QVERIFY(!tab->security()->certificateErrorPending());
    QCOMPARE(acceptSpy.count(), 1);
}

void TestTabSecurity::overrideKeepsTheErrorStateWhenComingBack()
{
    TabModel model;
    const QUrl failedUrl(QStringLiteral("https://expired.example/"));
    Tab *tab = acceptedErrorTab(model, failedUrl);

    tab->setUrl(QUrl(QStringLiteral("https://other.example/")));
    QCOMPARE(tab->security()->state(), QStringLiteral("secure"));
    tab->setUrl(failedUrl);

    QCOMPARE(tab->security()->state(), QStringLiteral("error"));
}

void TestTabSecurity::overrideReachesEveryTabOfTheSameProfile()
{
    TabModel model;
    const QUrl failedUrl(QStringLiteral("https://expired.example/"));
    Tab *tab = acceptedErrorTab(model, failedUrl);

    Tab *sameProfile = model.addTab(false, failedUrl);

    QCOMPARE(sameProfile->profile(), tab->profile());
    QCOMPARE(sameProfile->security()->state(), QStringLiteral("error"));
}

void TestTabSecurity::privateTabNeverInheritsTheOverride()
{
    TabModel model;
    const QUrl failedUrl(QStringLiteral("https://expired.example/"));
    Tab *tab = acceptedErrorTab(model, failedUrl);

    Tab *privateTab = model.addTab(true, failedUrl);

    QVERIFY(privateTab->profile() != tab->profile());
    QCOMPARE(privateTab->security()->state(), QStringLiteral("secure"));
}

void TestTabSecurity::rejectCertificateErrorClearsThePendingError()
{
    TabModel model;
    Tab *tab = model.addTab();
    QSignalSpy rejectSpy(tab->security(), &TabSecurity::rejectCertificateErrorRequested);

    tab->security()->setPendingCertificateError(QUrl(QStringLiteral("https://bad.example/")),
                                    QStringLiteral("Bad certificate"), true);
    tab->security()->rejectCertificateError();

    QVERIFY(!tab->security()->certificateErrorPending());
    QCOMPARE(rejectSpy.count(), 1);
}

int main(int argc, char *argv[])
{
    QStandardPaths::setTestModeEnabled(true);
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();

    QGuiApplication app(argc, argv);
    TestTabSecurity test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_tabsecurity.moc"
