#include <QTest>

#include "browser/suggestionlist.h"

class TestSuggestionList : public QObject
{
    Q_OBJECT

private slots:
    void keepsAtMostSixSuggestions();
    void skipsEmptyAndNonStringEntries();
    void returnsNothingForUnexpectedJson();
};

void TestSuggestionList::keepsAtMostSixSuggestions()
{
    const QStringList items = suggestionsFromJson(
            R"(["q",["a","b","c","d","e","f","g","h"]])");

    QCOMPARE(items, (QStringList{"a", "b", "c", "d", "e", "f"}));
}

void TestSuggestionList::skipsEmptyAndNonStringEntries()
{
    const QStringList items = suggestionsFromJson(R"(["q",["a","",1,null,"b"]])");

    QCOMPARE(items, (QStringList{"a", "b"}));
}

void TestSuggestionList::returnsNothingForUnexpectedJson()
{
    QVERIFY(suggestionsFromJson("not json").isEmpty());
    QVERIFY(suggestionsFromJson(R"({"a":1})").isEmpty());
    QVERIFY(suggestionsFromJson(R"(["q"])").isEmpty());
    QVERIFY(suggestionsFromJson(R"(["q","text"])").isEmpty());
}

QTEST_APPLESS_MAIN(TestSuggestionList)

#include "tst_suggestionlist.moc"
