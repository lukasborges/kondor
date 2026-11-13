#include <QTest>

#include "bookmarks/bookmarkhtmlparser.h"

class TestBookmarkHtmlParser : public QObject
{
    Q_OBJECT

private slots:
    void parsesNestedFolders();
    void skipsCommentsAndUnsupportedSchemes();
    void decodesEntitiesInTitles();
    void usesUrlWhenTitleIsEmpty();
};

void TestBookmarkHtmlParser::parsesNestedFolders()
{
    const ParsedBookmarks parsed = BookmarkHtmlParser::parse(QStringLiteral(
        "<DL><p><DT><H3>Outer</H3><DL><p>"
        "<DT><A HREF=\"https://kde.org/\">KDE</A>"
        "<DT><H3>Inner</H3><DL><p><DT><A HREF=\"https://qt.io/\">Qt</A></DL><p>"
        "</DL><p><DT><A HREF=\"https://example.org/\">Top</A></DL><p>"));
    QCOMPARE(parsed.bookmarkCount, 3);
    QCOMPARE(parsed.root.children.size(), 2);
    const ImportedBookmark &outer = parsed.root.children.at(0);
    QVERIFY(outer.isFolder);
    QCOMPARE(outer.title, QStringLiteral("Outer"));
    QCOMPARE(outer.children.size(), 2);
    QCOMPARE(outer.children.at(1).children.at(0).title, QStringLiteral("Qt"));
    QCOMPARE(parsed.root.children.at(1).title, QStringLiteral("Top"));
}

void TestBookmarkHtmlParser::skipsCommentsAndUnsupportedSchemes()
{
    const ParsedBookmarks parsed = BookmarkHtmlParser::parse(QStringLiteral(
        "<DL><!-- <A HREF=\"https://hidden.example/\">Hidden</A> -->"
        "<DT><A HREF=\"place:type=6\">Place</A>"
        "<DT><A HREF=\"javascript:alert(1)\">Script</A>"
        "<DT><A HREF=\"https://kde.org/\">KDE</A></DL>"));
    QCOMPARE(parsed.bookmarkCount, 1);
    QCOMPARE(parsed.root.children.size(), 1);
    QCOMPARE(parsed.root.children.at(0).url, QUrl(QStringLiteral("https://kde.org/")));
}

void TestBookmarkHtmlParser::decodesEntitiesInTitles()
{
    const ParsedBookmarks parsed = BookmarkHtmlParser::parse(QStringLiteral(
        "<DL><DT><A HREF=\"https://kde.org/\">KDE &amp; Qt &#128512; &#x1F600; &#0; <b>bold</b></A></DL>"));
    QCOMPARE(parsed.root.children.size(), 1);
    const QString expected = QStringLiteral("KDE & Qt ") + QString::fromUcs4(U"\U0001F600")
        + QLatin1Char(' ') + QString::fromUcs4(U"\U0001F600") + QStringLiteral(" &#0; bold");
    QCOMPARE(parsed.root.children.at(0).title, expected);
}

void TestBookmarkHtmlParser::usesUrlWhenTitleIsEmpty()
{
    const ParsedBookmarks parsed = BookmarkHtmlParser::parse(
        QStringLiteral("<DL><DT><A HREF=\"https://kde.org/\">  </A></DL>"));
    QCOMPARE(parsed.root.children.size(), 1);
    QCOMPARE(parsed.root.children.at(0).title, QStringLiteral("https://kde.org/"));
}

QTEST_APPLESS_MAIN(TestBookmarkHtmlParser)

#include "tst_bookmarkhtmlparser.moc"
