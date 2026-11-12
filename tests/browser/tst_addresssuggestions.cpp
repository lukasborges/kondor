#include <QGuiApplication>
#include <QSet>
#include <QJSEngine>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickItem>
#include <QQuickStyle>
#include <QTemporaryDir>
#include <QSignalSpy>
#include <QSqlQuery>
#include <QTest>
#include <QVariantList>
#include <QVariantMap>

#include "bookmarks/bookmarkmanager.h"
#include "core/database.h"
#include "browser/faviconstore.h"
#include "history/historymanager.h"
#include "browser/profilemanager.h"
#include "core/settings.h"

// Builds the address bar dropdown from the real singletons and checks the
// row order, limits and activation URLs of #44 and #11.
class TestAddressSuggestions : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void init();
    void cleanupTestCase();
    void visitAndSearchRows();
    void addsBookmarksHistoryAndNetworkSuggestions();
    void limitsRowsAndSkipsDuplicates();
    void activateEmitsTheRowUrl();

private:
    QObject *createPopup();
    void addHistory(const QString &url, const QString &title, qint64 visitedAt);
    QVariantList rowsOf(QObject *popup) const;

    QQmlEngine m_engine;
};

void TestAddressSuggestions::initTestCase()
{
    QVERIFY2(Database::instance()->isValid(), "the test database must open");

    qmlRegisterSingletonType<ProfileManager>("Kondor", 1, 0, "ProfileManager",
                                             [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                 return ProfileManager::instance();
                                             });
    qmlRegisterSingletonType<HistoryManager>("Kondor", 1, 0, "HistoryManager",
                                             [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                 return HistoryManager::instance();
                                             });
    qmlRegisterSingletonType<BookmarkManager>("Kondor", 1, 0, "BookmarkManager",
                                              [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                  return BookmarkManager::instance();
                                              });
    qmlRegisterSingletonType<FaviconStore>("Kondor", 1, 0, "FaviconStore",
                                           [](QQmlEngine *, QJSEngine *) -> QObject * {
                                               return FaviconStore::instance();
                                           });
    qmlRegisterSingletonType<Settings>("Kondor", 1, 0, "Settings",
                                       [](QQmlEngine *, QJSEngine *) -> QObject * {
                                           return Settings::instance();
                                       });
}

void TestAddressSuggestions::init()
{
    QSqlQuery clear(Database::instance()->handle());
    QVERIFY(clear.exec(QStringLiteral("DELETE FROM history")));
}

void TestAddressSuggestions::cleanupTestCase()
{
}

QObject *TestAddressSuggestions::createPopup()
{
    m_engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));
    QQmlComponent component(&m_engine,
                            QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR
                                                               "/browser/AddressSuggestions.qml")));
    QObject *popup = component.create();
    if (!popup)
        qWarning() << component.errors();
    return popup;
}

void TestAddressSuggestions::addHistory(const QString &url, const QString &title,
                                        qint64 visitedAt)
{
    QSqlQuery insert(Database::instance()->handle());
    insert.prepare(QStringLiteral(
        "INSERT INTO history (url, title, visited_at) VALUES (?, ?, ?)"));
    insert.addBindValue(url);
    insert.addBindValue(title);
    insert.addBindValue(visitedAt);
    QVERIFY(insert.exec());
}

QVariantList TestAddressSuggestions::rowsOf(QObject *popup) const
{
    return popup->property("rows").toList();
}

void TestAddressSuggestions::visitAndSearchRows()
{
    QObject *popup = createPopup();
    QVERIFY(popup);
    popup->setProperty("text", QStringLiteral("kde.org"));

    // The seeded default bookmarks also match "kde.org"; only the first two
    // rows are the #44 visit/search pair.
    const QVariantList rows = rowsOf(popup);
    QVERIFY(rows.size() >= 2);
    QCOMPARE(rows.at(0).toMap().value(QStringLiteral("url")).toString(),
             QStringLiteral("https://kde.org"));
    QCOMPARE(rows.at(0).toMap().value(QStringLiteral("suffix")).toString(),
             QStringLiteral("Visit"));
    QCOMPARE(rows.at(0).toMap().value(QStringLiteral("fieldText")).toString(),
             QStringLiteral("https://kde.org"));
    QCOMPARE(rows.at(1).toMap().value(QStringLiteral("iconName")).toString(),
             QStringLiteral("edit-find"));
    QVERIFY(rows.at(1).toMap().value(QStringLiteral("url")).toString()
                .startsWith(QStringLiteral("https://duckduckgo.com/")));
    // Selecting the search row shows the typed text, not the engine URL.
    QCOMPARE(rows.at(1).toMap().value(QStringLiteral("fieldText")).toString(),
             QStringLiteral("kde.org"));

    QVariant selected;
    QVERIFY(QMetaObject::invokeMethod(popup, "selectedText", Q_RETURN_ARG(QVariant, selected),
                                      Q_ARG(QVariant, 1)));
    QCOMPARE(selected.toString(), QStringLiteral("kde.org"));

    popup->setProperty("text", QStringLiteral("plasma"));
    const QVariantList searchOnly = rowsOf(popup);
    QCOMPARE(searchOnly.size(), 1);
    QCOMPARE(searchOnly.at(0).toMap().value(QStringLiteral("suffix")).toString(),
             QStringLiteral("Search with DuckDuckGo"));

    popup->setProperty("text", QStringLiteral("   "));
    QVERIFY(rowsOf(popup).isEmpty());
    delete popup;
}

void TestAddressSuggestions::addsBookmarksHistoryAndNetworkSuggestions()
{
    const qint64 now = 1000000;
    addHistory(QStringLiteral("https://kde.org/"), QStringLiteral("KDE Community"), now - 3000);
    addHistory(QStringLiteral("https://kde.org/"), QStringLiteral("KDE Community"), now - 2000);
    addHistory(QStringLiteral("https://plasma.kde.org/"), QStringLiteral("KDE Plasma"),
               now - 1000);

    BookmarkManager *bookmarks = BookmarkManager::instance();
    const qint64 folder = bookmarks->addFolder(QStringLiteral("Address suggestions test"),
                                               bookmarks->otherFolderId());
    QVERIFY(bookmarks->addBookmark(QUrl(QStringLiteral("https://kde.org/hig/")),
                                   QStringLiteral("Plasma HIG"), folder) > 0);

    QObject *popup = createPopup();
    QVERIFY(popup);
    popup->setProperty("text", QStringLiteral("plasma"));

    const QVariantList rows = rowsOf(popup);
    // Search row, then bookmarks and history.
    QVERIFY(rows.size() >= 3);
    QCOMPARE(rows.at(0).toMap().value(QStringLiteral("iconName")).toString(),
             QStringLiteral("edit-find"));

    bool sawBookmark = false;
    bool sawHig = false;
    for (const QVariant &row : rows) {
        const QVariantMap entry = row.toMap();
        if (entry.value(QStringLiteral("iconName")).toString() == QLatin1String("bookmarks")) {
            sawBookmark = true;
            if (entry.value(QStringLiteral("label")).toString() == QLatin1String("Plasma HIG"))
                sawHig = true;
        }
    }
    QVERIFY(sawBookmark);
    QVERIFY(sawHig);

    bool sawHistory = false;
    for (const QVariant &row : rows) {
        if (row.toMap().value(QStringLiteral("iconName")).toString()
                == QLatin1String("view-history")) {
            sawHistory = true;
        }
    }
    QVERIFY(sawHistory);

    popup->setProperty("networkSuggestions",
                       QVariantList{QStringLiteral("kde connect"),
                                    QStringLiteral("kde plasma 6")});
    const QVariantList withSuggestions = rowsOf(popup);
    QCOMPARE(withSuggestions.size(), rows.size() + 2);
    const QVariantMap last = withSuggestions.last().toMap();
    QCOMPARE(last.value(QStringLiteral("label")).toString(), QStringLiteral("kde plasma 6"));
    QCOMPARE(last.value(QStringLiteral("fieldText")).toString(),
             QStringLiteral("kde plasma 6"));
    QCOMPARE(last.value(QStringLiteral("url")).toString(),
             ProfileManager::instance()->searchUrl(QStringLiteral("kde plasma 6")).toString());

    // Editing the text drops the answers for the previous text.
    popup->setProperty("text", QStringLiteral("plasma p"));
    for (const QVariant &row : rowsOf(popup)) {
        QVERIFY(row.toMap().value(QStringLiteral("label")).toString()
                != QLatin1String("kde connect"));
    }

    bookmarks->remove(folder);
    delete popup;
}

void TestAddressSuggestions::limitsRowsAndSkipsDuplicates()
{
    for (int i = 0; i < 15; ++i) {
        addHistory(QStringLiteral("https://example%1.org/").arg(i),
                   QStringLiteral("Example %1").arg(i), 1000000 + i);
    }
    // The same URL twice in history and as a bookmark must appear once.
    addHistory(QStringLiteral("https://example0.org/"), QStringLiteral("Example 0"), 2000000);

    QObject *popup = createPopup();
    QVERIFY(popup);
    popup->setProperty("text", QStringLiteral("example"));

    const QVariantList rows = rowsOf(popup);
    QVERIFY(rows.size() <= 10);
    QSet<QString> urls;
    for (const QVariant &row : rows) {
        const QString url = row.toMap().value(QStringLiteral("url")).toString();
        QVERIFY2(!urls.contains(url), qPrintable(url));
        urls.insert(url);
    }
    delete popup;
}

void TestAddressSuggestions::activateEmitsTheRowUrl()
{
    QObject *popup = createPopup();
    QVERIFY(popup);
    popup->setProperty("text", QStringLiteral("example.com"));

    const QVariantList rows = rowsOf(popup);
    QCOMPARE(rows.size(), 2);
    QCOMPARE(rows.at(0).toMap().value(QStringLiteral("url")).toString(),
             QStringLiteral("https://example.com"));

    QSignalSpy spy(popup, SIGNAL(navigate(QUrl,bool)));
    QVERIFY(spy.isValid());

    const bool invoked = QMetaObject::invokeMethod(popup, "activate", Q_ARG(QVariant, 0),
                                                  Q_ARG(QVariant, true));
    QVERIFY(invoked);
    QCOMPARE(spy.count(), 1);
    QCOMPARE(spy.at(0).at(0).toUrl(), QUrl(QStringLiteral("https://example.com")));
    QCOMPARE(spy.at(0).at(1).toBool(), true);
    delete popup;
}

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);

    // Never touch the real profile: the database and settings live here.
    QTemporaryDir home;
    if (!home.isValid())
        return 1;
    qputenv("XDG_DATA_HOME", home.path().toUtf8());
    qputenv("XDG_CONFIG_HOME", home.path().toUtf8());
    qputenv("XDG_CACHE_HOME", home.path().toUtf8());

    QGuiApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE-Test"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor-AddressSuggestions-Test"));
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));

    TestAddressSuggestions test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_addresssuggestions.moc"
