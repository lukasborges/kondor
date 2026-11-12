#include <QGuiApplication>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickItem>
#include <QQuickStyle>
#include <QTemporaryDir>
#include <QTest>
#include <QtWebEngineCore/qwebenginecontextmenurequest.h>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "browser/profilemanager.h"
#include "browser/tab.h"
#include "browser/tabmodel.h"
#include "core/settings.h"
#include "pagecontextmenucases.h"

namespace {
QVariantMap completeRequest(const QVariantMap &given)
{
    QVariantMap request{ { QStringLiteral("linkUrl"), QUrl() },
                         { QStringLiteral("mediaUrl"), QUrl() },
                         { QStringLiteral("mediaType"), int(Request::MediaTypeNone) },
                         { QStringLiteral("mediaFlags"), 0 },
                         { QStringLiteral("editFlags"), 0 },
                         { QStringLiteral("isContentEditable"), false },
                         { QStringLiteral("selectedText"), QString() },
                         { QStringLiteral("misspelledWord"), QString() },
                         { QStringLiteral("spellCheckerSuggestions"), QStringList() } };
    request.insert(given);
    return request;
}

const char *kHostQml = R"(
import QtQuick
import QtWebEngine
import Kondor

Item {
    property var menu: pageMenu
    WebEngineView { id: view }
    PageContextMenu { id: pageMenu; webView: view }
}
)";

}

class TestPageContextMenu : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanupTestCase();
    void showsTheBlocksOfTheRequest_data();
    void showsTheBlocksOfTheRequest();
    void neverDoublesOrEndsWithASeparator();

private:
    QStringList itemsFor(const QVariant &request);
    QQmlEngine m_engine;
    QObject *m_host = nullptr;
};

void TestPageContextMenu::initTestCase()
{
    qmlRegisterType<TabModel>("Kondor", 1, 0, "TabModel");
    qmlRegisterUncreatableType<Tab>("Kondor", 1, 0, "Tab", QStringLiteral("Tabs come from TabModel"));
    qmlRegisterSingletonType<Settings>("Kondor", 1, 0, "Settings",
                                       [](QQmlEngine *, QJSEngine *) -> QObject * {
                                           return Settings::instance();
                                       });
    qmlRegisterSingletonType<ProfileManager>("Kondor", 1, 0, "ProfileManager",
                                             [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                 return ProfileManager::instance();
                                             });
    Settings::instance()->setSpellCheckEnabled(false);
    m_engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));
    QQmlComponent component(&m_engine);
    component.setData(kHostQml, QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR "/Host.qml")));
    m_host = component.create();
    if (!m_host)
        qWarning() << component.errors();
    QVERIFY(m_host);
}

void TestPageContextMenu::cleanupTestCase()
{
    delete m_host;
}

QStringList TestPageContextMenu::itemsFor(const QVariant &request)
{
    auto *menu = m_host->property("menu").value<QObject *>();
    menu->setProperty("request", completeRequest(request.toMap()));
    QMetaObject::invokeMethod(menu, "rebuild");
    QStringList items;
    for (int i = 0; i < menu->property("count").toInt(); ++i) {
        QQuickItem *item = nullptr;
        QMetaObject::invokeMethod(menu, "itemAt", Q_RETURN_ARG(QQuickItem *, item), Q_ARG(int, i));
        const bool isSeparator = QString::fromLatin1(item->metaObject()->className())
                                         .contains(QLatin1String("MenuSeparator"));
        items << (isSeparator ? kSeparator : item->property("text").toString());
    }
    return items;
}

void TestPageContextMenu::showsTheBlocksOfTheRequest_data()
{
    QTest::addColumn<QVariantMap>("request");
    QTest::addColumn<QStringList>("items");
    for (const Case &row : kCases) {
        QStringList items = row.items;
        items.replaceInStrings(QStringLiteral("%SEARCH%"), searchItem());
        QTest::newRow(row.name) << row.request << items;
    }
}

void TestPageContextMenu::showsTheBlocksOfTheRequest()
{
    QFETCH(QVariantMap, request);
    QFETCH(QStringList, items);
    QCOMPARE(itemsFor(request), items);
}

void TestPageContextMenu::neverDoublesOrEndsWithASeparator()
{
    QList<QVariant> requests{ QVariant() };
    for (const Case &row : kCases)
        requests << row.request;
    for (const QVariant &request : requests) {
        const QStringList items = itemsFor(request);
        QVERIFY(items.first() != kSeparator);
        QVERIFY(items.last() != kSeparator);
        for (qsizetype i = 1; i < items.size(); ++i)
            QVERIFY(!(items[i] == kSeparator && items[i - 1] == kSeparator));
    }
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
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));

    TestPageContextMenu test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_pagecontextmenu.moc"
