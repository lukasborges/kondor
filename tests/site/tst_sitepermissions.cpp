#include <QGuiApplication>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickStyle>
#include <QQuickWebEngineProfile>
#include <QQuickWindow>
#include <QSignalSpy>
#include <QTemporaryDir>
#include <QTest>
#include <QWebEnginePermission>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "browser/profilemanager.h"
#include "browser/tab.h"

namespace {
QObject *findByClassName(QObject *parent, const QString &className)
{
    for (QObject *child : parent->children()) {
        if (QString::fromLatin1(child->metaObject()->className()).contains(className))
            return child;
        if (QObject *found = findByClassName(child, className))
            return found;
    }
    return nullptr;
}
}

// Covers the queue behind the permission bar and the list in the Site
// Permissions window. QWebEnginePermission objects cannot be constructed
// directly, so the tests query them from a profile, which works even before
// the site ever asked.
class TestSitePermissions : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void profilesStoreNormalDecisionsAndKeepPrivateOnesInMemory();
    void answersQueuedPermissionsInOrder();
    void navigatingAwayDeniesPendingPermissions();
    void navigatingWithinSameOriginKeepsPendingPermissions();
    void requestBarShowsAndAnswersThePendingPermission();
    void dialogListsAndRevokesDecisions();

private:
    QQmlEngine m_engine;
};

void TestSitePermissions::initTestCase()
{
    qmlRegisterSingletonType<ProfileManager>("Kondor", 1, 0, "ProfileManager",
                                             [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                 return ProfileManager::instance();
                                             });
    qmlRegisterUncreatableType<Tab>("Kondor", 1, 0, "Tab",
                                    QStringLiteral("Tabs are created by TabModel"));
}

void TestSitePermissions::profilesStoreNormalDecisionsAndKeepPrivateOnesInMemory()
{
    QQuickWebEngineProfile *normal = ProfileManager::instance()->defaultProfile();
    QCOMPARE(normal->persistentPermissionsPolicy(),
             QQuickWebEngineProfile::PersistentPermissionsPolicy::StoreOnDisk);

    QQuickWebEngineProfile *privateProfile = ProfileManager::instance()->createPrivateProfile();
    QVERIFY(privateProfile->isOffTheRecord());
    QCOMPARE(privateProfile->persistentPermissionsPolicy(),
             QQuickWebEngineProfile::PersistentPermissionsPolicy::StoreInMemory);
}

void TestSitePermissions::answersQueuedPermissionsInOrder()
{
    QQuickWebEngineProfile profile;
    profile.setPersistentPermissionsPolicy(
            QQuickWebEngineProfile::PersistentPermissionsPolicy::StoreInMemory);
    Tab tab(&profile);

    const QUrl origin(QStringLiteral("https://queue.example"));
    const QWebEnginePermission geolocation =
            profile.queryPermission(origin, QWebEnginePermission::PermissionType::Geolocation);
    const QWebEnginePermission notifications =
            profile.queryPermission(origin, QWebEnginePermission::PermissionType::Notifications);

    QSignalSpy spy(&tab, &Tab::pendingPermissionChanged);
    tab.enqueuePermission(geolocation);
    tab.enqueuePermission(notifications);
    QCOMPARE(spy.count(), 1);

    QVERIFY(tab.pendingPermission().isValid());
    QCOMPARE(int(tab.pendingPermission().value<QWebEnginePermission>().permissionType()),
             int(QWebEnginePermission::PermissionType::Geolocation));

    tab.answerPermission(true);
    QCOMPARE(spy.count(), 2);
    QCOMPARE(profile.queryPermission(origin, QWebEnginePermission::PermissionType::Geolocation).state(),
             QWebEnginePermission::State::Granted);
    QCOMPARE(int(tab.pendingPermission().value<QWebEnginePermission>().permissionType()),
             int(QWebEnginePermission::PermissionType::Notifications));

    tab.answerPermission(false);
    QCOMPARE(spy.count(), 3);
    QCOMPARE(profile.queryPermission(origin, QWebEnginePermission::PermissionType::Notifications).state(),
             QWebEnginePermission::State::Denied);
    QVERIFY(!tab.pendingPermission().isValid());
}

void TestSitePermissions::navigatingAwayDeniesPendingPermissions()
{
    QQuickWebEngineProfile profile;
    profile.setPersistentPermissionsPolicy(
            QQuickWebEngineProfile::PersistentPermissionsPolicy::StoreInMemory);
    Tab tab(&profile);

    const QUrl origin(QStringLiteral("https://leave.example"));
    tab.setUrl(origin);
    tab.enqueuePermission(
            profile.queryPermission(origin, QWebEnginePermission::PermissionType::Geolocation));

    tab.setUrl(QUrl(QStringLiteral("https://other.example/")));

    QCOMPARE(profile.queryPermission(origin, QWebEnginePermission::PermissionType::Geolocation).state(),
             QWebEnginePermission::State::Denied);
    QVERIFY(!tab.pendingPermission().isValid());
}

void TestSitePermissions::navigatingWithinSameOriginKeepsPendingPermissions()
{
    QQuickWebEngineProfile profile;
    profile.setPersistentPermissionsPolicy(
            QQuickWebEngineProfile::PersistentPermissionsPolicy::StoreInMemory);
    Tab tab(&profile);

    const QUrl permissionOrigin(QStringLiteral("https://stay.example"));
    tab.setUrl(QUrl(QStringLiteral("https://stay.example/meet")));
    tab.enqueuePermission(
            profile.queryPermission(permissionOrigin, QWebEnginePermission::PermissionType::Geolocation));

    // Same-document changes and same-origin navigations keep the prompt.
    tab.setUrl(QUrl(QStringLiteral("https://stay.example/meet#room")));
    QVERIFY(tab.pendingPermission().isValid());
    tab.setUrl(QUrl(QStringLiteral("https://stay.example/meet/room")));
    QVERIFY(tab.pendingPermission().isValid());
    QCOMPARE(profile.queryPermission(permissionOrigin, QWebEnginePermission::PermissionType::Geolocation).state(),
             QWebEnginePermission::State::Ask);

    // A different origin still denies it.
    tab.setUrl(QUrl(QStringLiteral("https://elsewhere.example/")));
    QCOMPARE(profile.queryPermission(permissionOrigin, QWebEnginePermission::PermissionType::Geolocation).state(),
             QWebEnginePermission::State::Denied);
    QVERIFY(!tab.pendingPermission().isValid());
}

void TestSitePermissions::requestBarShowsAndAnswersThePendingPermission()
{
    QQuickWebEngineProfile profile;
    profile.setPersistentPermissionsPolicy(
            QQuickWebEngineProfile::PersistentPermissionsPolicy::StoreInMemory);
    Tab tab(&profile);

    const QUrl origin(QStringLiteral("https://meet.example"));
    tab.enqueuePermission(
            profile.queryPermission(origin, QWebEnginePermission::PermissionType::Geolocation));

    m_engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));

    QQmlComponent component(&m_engine,
                            QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR
                                                               "/site/PermissionBar.qml")));
    QObject *object = component.createWithInitialProperties(
            { { QStringLiteral("tab"), QVariant::fromValue(&tab) } });
    if (!object) {
        qWarning() << component.errors();
        QFAIL("the permission bar must load");
    }
    QCOMPARE(object->property("visible").toBool(), true);

    QObject *text = findByClassName(object, QStringLiteral("Label"));
    QVERIFY(text);
    QVERIFY(text->property("text").toString().contains(QStringLiteral("meet.example")));
    QVERIFY(text->property("text").toString().contains(QStringLiteral("location")));

    tab.answerPermission(true);
    QCOMPARE(object->property("visible").toBool(), false);
    QCOMPARE(profile.queryPermission(origin, QWebEnginePermission::PermissionType::Geolocation).state(),
             QWebEnginePermission::State::Granted);

    delete object;
}

void TestSitePermissions::dialogListsAndRevokesDecisions()
{
    QQuickWebEngineProfile *profile = ProfileManager::instance()->defaultProfile();
    const QUrl origin(QStringLiteral("https://permissions.example"));
    profile->queryPermission(origin, QWebEnginePermission::PermissionType::Geolocation).grant();

    m_engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));

    QQmlComponent component(&m_engine,
                            QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR
                                                               "/site/SitePermissionsDialog.qml")));
    QObject *object = component.create();
    if (!object) {
        qWarning() << component.errors();
        QFAIL("the Site Permissions window must load");
    }
    auto *window = qobject_cast<QQuickWindow *>(object);
    QVERIFY(window);
    QMetaObject::invokeMethod(window, "showWindow");
    QVERIFY(window->isVisible());

    QVariantList rows = window->property("rows").toList();
    QCOMPARE(rows.size(), 1);
    const QVariantMap row = rows.first().toMap();
    QCOMPARE(row.value(QStringLiteral("site")).toString(), QStringLiteral("permissions.example"));
    QCOMPARE(row.value(QStringLiteral("perm")).toString(), QStringLiteral("Location"));
    QCOMPARE(row.value(QStringLiteral("granted")).toBool(), true);

    const QVariant permission = row.value(QStringLiteral("permission"));
    QVERIFY(permission.value<QWebEnginePermission>().isValid());
    QMetaObject::invokeMethod(window, "revoke", Q_ARG(QVariant, permission));

    QCOMPARE(window->property("rows").toList().size(), 0);
    QCOMPARE(profile->queryPermission(origin, QWebEnginePermission::PermissionType::Geolocation).state(),
             QWebEnginePermission::State::Ask);

    delete window;
}

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();

    // Never touch the real profile: settings and permissions live in the
    // temporary home.
    QTemporaryDir home;
    if (!home.isValid())
        return 1;
    qputenv("XDG_DATA_HOME", home.path().toUtf8());
    qputenv("XDG_CONFIG_HOME", home.path().toUtf8());
    qputenv("XDG_CACHE_HOME", home.path().toUtf8());

    QGuiApplication app(argc, argv);
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));

    TestSitePermissions test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_sitepermissions.moc"
