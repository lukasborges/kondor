#include <QGuiApplication>
#include <QQuickStyle>
#include <QSet>
#include <QSignalSpy>
#include <QTemporaryDir>

#include "addresssuggestionsharness.h"
#include "common/isolatedhome.h"

class TestAddressSuggestions : public AddressSuggestionsFixture
{
    Q_OBJECT

private slots:
    void initTestCase() { registerSuggestionTypes(); }
    void init() { clearHistory(); }
    void visitRowComesFirst();
    void searchRowFollowsTheVisitRow();
    void searchRowShowsTheTypedText();
    void plainWordOffersOnlyTheSearchRow();
    void blankTextHasNoRows();
    void addsBookmarkRows();
    void addsHistoryRows();
    void addsNetworkSuggestionRows();
    void editingTheTextDropsNetworkSuggestions();
    void keepsTheRowOrder();
    void limitsRowsAndSkipsDuplicates();
    void activateEmitsTheRowUrl();
};

void TestAddressSuggestions::visitRowComesFirst()
{
    const auto popup = popupTyping(QStringLiteral("kde.org"));
    const QVariantList rows = rowsOf(popup.get());
    QVERIFY(rows.size() >= 2);
    QCOMPARE(fieldOf(rows, 0, "url"), QStringLiteral("https://kde.org"));
    QCOMPARE(fieldOf(rows, 0, "suffix"), QStringLiteral("Visit"));
    QCOMPARE(fieldOf(rows, 0, "fieldText"), QStringLiteral("https://kde.org"));
}

void TestAddressSuggestions::searchRowFollowsTheVisitRow()
{
    const auto popup = popupTyping(QStringLiteral("kde.org"));
    const QVariantList rows = rowsOf(popup.get());
    QVERIFY(rows.size() >= 2);
    QCOMPARE(fieldOf(rows, 1, "iconName"), QStringLiteral("edit-find"));
    QVERIFY(fieldOf(rows, 1, "url").startsWith(QStringLiteral("https://duckduckgo.com/")));
}

void TestAddressSuggestions::searchRowShowsTheTypedText()
{
    const auto popup = popupTyping(QStringLiteral("kde.org"));
    QCOMPARE(fieldOf(rowsOf(popup.get()), 1, "fieldText"), QStringLiteral("kde.org"));

    QVariant selected;
    QVERIFY(QMetaObject::invokeMethod(popup.get(), "selectedText",
                                      Q_RETURN_ARG(QVariant, selected), Q_ARG(QVariant, 1)));
    QCOMPARE(selected.toString(), QStringLiteral("kde.org"));
}

void TestAddressSuggestions::plainWordOffersOnlyTheSearchRow()
{
    const auto popup = popupTyping(QStringLiteral("plasma"));
    const QVariantList rows = rowsOf(popup.get());
    QCOMPARE(rows.size(), 1);
    QCOMPARE(fieldOf(rows, 0, "suffix"), QStringLiteral("Search with DuckDuckGo"));
}

void TestAddressSuggestions::blankTextHasNoRows()
{
    const auto popup = popupTyping(QStringLiteral("   "));
    QVERIFY(rowsOf(popup.get()).isEmpty());
}

void TestAddressSuggestions::addsBookmarkRows()
{
    addPlasmaHistory();
    SeededBookmarkFolder folder(addPlasmaBookmark());
    const auto popup = popupTyping(QStringLiteral("plasma"));
    const QVariantList rows = rowsOf(popup.get());
    QVERIFY(hasRowWithIcon(rows, "bookmarks"));
    QVERIFY(hasRowWithIconAndLabel(rows, "bookmarks", "Plasma HIG"));
}

void TestAddressSuggestions::addsHistoryRows()
{
    addPlasmaHistory();
    SeededBookmarkFolder folder(addPlasmaBookmark());
    const auto popup = popupTyping(QStringLiteral("plasma"));
    QVERIFY(hasRowWithIcon(rowsOf(popup.get()), "view-history"));
}

void TestAddressSuggestions::addsNetworkSuggestionRows()
{
    addPlasmaHistory();
    SeededBookmarkFolder folder(addPlasmaBookmark());
    const auto popup = popupTyping(QStringLiteral("plasma"));
    const int before = rowsOf(popup.get()).size();

    popup->setProperty("networkSuggestions", QVariantList{QStringLiteral("kde connect"),
                                                          QStringLiteral("kde plasma 6")});
    const QVariantList rows = rowsOf(popup.get());
    QCOMPARE(rows.size(), before + 2);
    QCOMPARE(fieldOf(rows, rows.size() - 1, "label"), QStringLiteral("kde plasma 6"));
    QCOMPARE(fieldOf(rows, rows.size() - 1, "fieldText"), QStringLiteral("kde plasma 6"));
    QCOMPARE(fieldOf(rows, rows.size() - 1, "url"),
             ProfileManager::instance()->searchUrl(QStringLiteral("kde plasma 6")).toString());
}

void TestAddressSuggestions::editingTheTextDropsNetworkSuggestions()
{
    const auto popup = popupTyping(QStringLiteral("plasma"));
    popup->setProperty("networkSuggestions", QVariantList{QStringLiteral("kde connect")});
    popup->setProperty("text", QStringLiteral("plasma p"));
    const QVariantList rows = rowsOf(popup.get());
    for (int row = 0; row < rows.size(); ++row)
        QVERIFY(fieldOf(rows, row, "label") != QLatin1String("kde connect"));
}

void TestAddressSuggestions::keepsTheRowOrder()
{
    addPlasmaHistory();
    SeededBookmarkFolder folder(addPlasmaBookmark());
    const auto popup = popupTyping(QStringLiteral("plasma"));
    const QVariantList rows = rowsOf(popup.get());
    QVERIFY(rows.size() >= 3);
    QCOMPARE(fieldOf(rows, 0, "iconName"), QStringLiteral("edit-find"));
}

void TestAddressSuggestions::limitsRowsAndSkipsDuplicates()
{
    for (int i = 0; i < 15; ++i) {
        addHistory(QStringLiteral("https://example%1.org/").arg(i),
                   QStringLiteral("Example %1").arg(i), 1000000 + i);
    }
    addHistory(QStringLiteral("https://example0.org/"), QStringLiteral("Example 0"), 2000000);

    const auto popup = popupTyping(QStringLiteral("example"));
    const QVariantList rows = rowsOf(popup.get());
    QVERIFY(rows.size() <= 10);
    QSet<QString> urls;
    for (int row = 0; row < rows.size(); ++row) {
        const QString url = fieldOf(rows, row, "url");
        QVERIFY2(!urls.contains(url), qPrintable(url));
        urls.insert(url);
    }
}

void TestAddressSuggestions::activateEmitsTheRowUrl()
{
    const auto popup = popupTyping(QStringLiteral("example.com"));
    const QVariantList rows = rowsOf(popup.get());
    QCOMPARE(rows.size(), 2);
    QCOMPARE(fieldOf(rows, 0, "url"), QStringLiteral("https://example.com"));

    QSignalSpy spy(popup.get(), SIGNAL(navigate(QUrl,bool)));
    QVERIFY(spy.isValid());
    const bool invoked = QMetaObject::invokeMethod(popup.get(), "activate", Q_ARG(QVariant, 0),
                                                  Q_ARG(QVariant, true));
    QVERIFY(invoked);
    QCOMPARE(spy.count(), 1);
    QCOMPARE(spy.at(0).at(0).toUrl(), QUrl(QStringLiteral("https://example.com")));
    QCOMPARE(spy.at(0).at(1).toBool(), true);
}

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);

    QTemporaryDir home;
    if (!useIsolatedHome(home))
        return 1;

    QGuiApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE-Test"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor-AddressSuggestions-Test"));
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));

    TestAddressSuggestions test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_addresssuggestions.moc"
