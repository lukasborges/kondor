#include <memory>

#include <QGuiApplication>
#include <QQuickStyle>
#include <QSignalSpy>
#include <QSqlQuery>
#include <QTemporaryDir>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "addressbarharness.h"

class TestAddressBar : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void init();
    void cleanup() { m_harness.reset(); }
    void completesAKnownHostInline();
    void backspaceAfterACompletionDoesNotCompleteAgain();
    void downAndUpMoveThroughTheSuggestions();
    void escapeRestoresTheTypedTextAndClosesTheSuggestions();
    void enterNavigatesTheCurrentTab();
    void switchingTheCurrentTabShowsItsUrl();

private:
    QQmlEngine m_engine;
    std::unique_ptr<AddressBarHarness> m_harness;
    bool isOpen() const { return m_harness->suggestions()->property("opened").toBool(); }
};

void TestAddressBar::initTestCase()
{
    QVERIFY2(Database::instance()->isValid(), "the test database must open");
    registerAddressBarTypes();
}

void TestAddressBar::init()
{
    m_harness = std::make_unique<AddressBarHarness>(m_engine);
    QSqlQuery clear(Database::instance()->handle());
    QVERIFY(clear.exec(QStringLiteral("DELETE FROM history")));
    QVERIFY(addHistoryVisit(QStringLiteral("https://kde.org/plasma")));
    QVERIFY(m_harness->open());
}

void TestAddressBar::completesAKnownHostInline()
{
    m_harness->type(QStringLiteral("kd"));
    QTRY_COMPARE(m_harness->text(), QStringLiteral("kde.org"));
    QCOMPARE(m_harness->bar()->property("selectedText").toString(), QStringLiteral("e.org"));
}

void TestAddressBar::backspaceAfterACompletionDoesNotCompleteAgain()
{
    m_harness->type(QStringLiteral("kd"));
    QTRY_COMPARE(m_harness->text(), QStringLiteral("kde.org"));

    m_harness->press(Qt::Key_Backspace);
    QTest::qWait(400);
    QCOMPARE(m_harness->text(), QStringLiteral("kd"));
}

void TestAddressBar::downAndUpMoveThroughTheSuggestions()
{
    m_harness->type(QStringLiteral("kd"));
    QTRY_VERIFY(isOpen());
    QTRY_COMPARE(m_harness->text(), QStringLiteral("kde.org"));
    QVERIFY(m_harness->suggestions()->property("rows").toList().size() >= 3);

    m_harness->press(Qt::Key_Down);
    m_harness->press(Qt::Key_Down);
    QCOMPARE(m_harness->suggestions()->property("currentIndex").toInt(), 2);
    QCOMPARE(m_harness->text(), m_harness->textOfRow(2));

    m_harness->press(Qt::Key_Up);
    QCOMPARE(m_harness->suggestions()->property("currentIndex").toInt(), 1);
    QCOMPARE(m_harness->text(), m_harness->textOfRow(1));
}

void TestAddressBar::escapeRestoresTheTypedTextAndClosesTheSuggestions()
{
    m_harness->type(QStringLiteral("kd"));
    QTRY_VERIFY(isOpen());
    m_harness->press(Qt::Key_Down);
    m_harness->press(Qt::Key_Down);
    QVERIFY(m_harness->text() != QStringLiteral("kd"));

    m_harness->press(Qt::Key_Escape);
    QCOMPARE(m_harness->text(), QStringLiteral("kd"));
    QVERIFY(!isOpen());
}

void TestAddressBar::enterNavigatesTheCurrentTab()
{
    QSignalSpy navigations(m_harness->tabs->currentTab(), &Tab::navigationRequested);
    m_harness->type(QStringLiteral("example.org"));
    m_harness->press(Qt::Key_Return);

    QCOMPARE(navigations.count(), 1);
    QCOMPARE(navigations.first().first().toUrl(),
             ProfileManager::instance()->resolveAddress(QStringLiteral("example.org")));
}

void TestAddressBar::switchingTheCurrentTabShowsItsUrl()
{
    QCOMPARE(m_harness->text(), QStringLiteral("https://kde.org/one"));

    m_harness->tabs->addTab(false, QUrl(QStringLiteral("https://example.org/two")));
    QTRY_COMPARE(m_harness->text(), QStringLiteral("https://example.org/two"));

    m_harness->tabs->setCurrentIndex(0);
    QTRY_COMPARE(m_harness->text(), QStringLiteral("https://kde.org/one"));
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
    QCoreApplication::setOrganizationName(QStringLiteral("KDE-Test"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor-AddressBar-Test"));
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));

    TestAddressBar test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_addressbar.moc"
