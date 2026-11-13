#include <QFile>
#include <QSignalSpy>
#include <QTest>
#include <QUrl>
#include <QVariant>
#include <QWebEnginePage>

namespace {
QString readScript(const QString &path)
{
    QFile file(path);
    return file.open(QIODevice::ReadOnly) ? QString::fromUtf8(file.readAll()) : QString();
}

const QString origin = QStringLiteral("http://localhost");

const QString fakeBridge = QStringLiteral(
    "window.__kondorChannel = Promise.resolve({ kondorPasswords: {"
    "  credentialsFor: (o, cb) => { window.__lookups = (window.__lookups || 0) + 1; cb([]); },"
    "  formSubmitted: () => {},"
    "  credentialsChanged: { connect: () => {} },"
    "  fillRequested: { connect: (f) => { window.__fill = f; } } } });");

const QString usernameStep = QStringLiteral(
    "<form><input type='text' name='q'><input type='email' name='who'><button>Next</button></form>");
const QString passwordStep = QStringLiteral(
    "<form><input type='text' name='user'><input type='password' name='pw'></form>");
const QString noUsernameField = QStringLiteral("<form><input type='number' name='age'></form>");
}

class TestPasswordFill : public QObject
{
    Q_OBJECT

private slots:
    void fillsUsernameOnUsernameOnlyStep();
    void fillsUsernameAndPasswordOnPasswordStep();
    void fillsNothingWithoutUsernameField();
    void looksUpCredentialsOnUsernameOnlyPage();
    void doesNotLookUpCredentialsWithoutLoginField();
    void looksUpCredentialsOnceWhenFieldAppearsLater();

private:
    QVariant evaluate(const QString &script);
    void loadPage(const QString &body);
    void requestFill();
    int lookupCount();

    QWebEnginePage m_page;
};

QVariant TestPasswordFill::evaluate(const QString &script)
{
    QVariant result;
    bool done = false;
    m_page.runJavaScript(script, [&](const QVariant &value) { result = value; done = true; });
    [&] { QTRY_VERIFY_WITH_TIMEOUT(done, 10000); }();
    return result;
}

void TestPasswordFill::loadPage(const QString &body)
{
    QSignalSpy loaded(&m_page, &QWebEnginePage::loadFinished);
    m_page.setHtml(body, QUrl(origin));
    QVERIFY(loaded.wait(10000));
    evaluate(fakeBridge);
    evaluate(readScript(QStringLiteral(":/scripts/usernamefield.js")));
    evaluate(readScript(QStringLiteral(":/scripts/passwords.js")));
    QTRY_VERIFY(evaluate(QStringLiteral("typeof window.__fill === 'function'")).toBool());
}

void TestPasswordFill::requestFill()
{
    evaluate(QStringLiteral("window.__fill('%1', 'ada@example.com', 'secret')").arg(origin));
}

void TestPasswordFill::fillsUsernameOnUsernameOnlyStep()
{
    loadPage(usernameStep);
    requestFill();
    QCOMPARE(evaluate(QStringLiteral("document.querySelector('[name=who]').value")).toString(),
             QStringLiteral("ada@example.com"));
    QCOMPARE(evaluate(QStringLiteral("document.querySelector('[name=q]').value")).toString(), QString());
}

void TestPasswordFill::fillsUsernameAndPasswordOnPasswordStep()
{
    loadPage(passwordStep);
    requestFill();
    QCOMPARE(evaluate(QStringLiteral("document.querySelector('[name=user]').value")).toString(),
             QStringLiteral("ada@example.com"));
    QCOMPARE(evaluate(QStringLiteral("document.querySelector('[name=pw]').value")).toString(),
             QStringLiteral("secret"));
}

void TestPasswordFill::fillsNothingWithoutUsernameField()
{
    loadPage(noUsernameField);
    requestFill();
    QCOMPARE(evaluate(QStringLiteral("document.querySelector('[name=age]').value")).toString(), QString());
}

int TestPasswordFill::lookupCount()
{
    return evaluate(QStringLiteral("window.__lookups || 0")).toInt();
}

void TestPasswordFill::looksUpCredentialsOnUsernameOnlyPage()
{
    loadPage(usernameStep);
    QCOMPARE(lookupCount(), 1);
}

void TestPasswordFill::doesNotLookUpCredentialsWithoutLoginField()
{
    loadPage(noUsernameField);
    QTest::qWait(600);
    QCOMPARE(lookupCount(), 0);
}

void TestPasswordFill::looksUpCredentialsOnceWhenFieldAppearsLater()
{
    loadPage(noUsernameField);
    evaluate(QStringLiteral("document.body.insertAdjacentHTML('beforeend', \"<input type='email' name='who'>\"); 0"));
    QTRY_COMPARE_WITH_TIMEOUT(lookupCount(), 1, 5000);
    evaluate(QStringLiteral("document.body.insertAdjacentHTML('beforeend', '<p>more</p>'); 0"));
    QTest::qWait(600);
    QCOMPARE(lookupCount(), 1);
}

QTEST_MAIN(TestPasswordFill)
#include "tst_passwordfill.moc"
