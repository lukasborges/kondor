#include <QGuiApplication>
#include <QQuickStyle>
#include <QSignalSpy>
#include <QTemporaryDir>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "../common/isolatedhome.h"
#include "sitepermissionsharness.h"

class TestSitePermissions : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void profilesStoreNormalDecisionsAndKeepPrivateOnesInMemory();
    void answersQueuedPermissionsInOrder();
    void navigatingAwayDeniesPendingPermissions();
    void navigatingWithinSameOriginKeepsPendingPermissions();
    void navigatingToAnotherOriginDeniesPendingPermissions();
};

void TestSitePermissions::initTestCase()
{
    registerSitePermissionTypes();
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
    PermissionFixture fixture;
    const QUrl origin(QStringLiteral("https://queue.example"));
    QSignalSpy spy(fixture.tab.permissions(), &TabPermissions::pendingChanged);
    fixture.enqueue(origin, PermissionType::Geolocation);
    fixture.enqueue(origin, PermissionType::Notifications);
    QCOMPARE(spy.count(), 1);
    QVERIFY(fixture.hasPending());
    QCOMPARE(fixture.pendingType(), int(PermissionType::Geolocation));
    fixture.tab.permissions()->answer(true);
    QCOMPARE(spy.count(), 2);
    QCOMPARE(fixture.stateOf(origin, PermissionType::Geolocation), PermissionState::Granted);
    QCOMPARE(fixture.pendingType(), int(PermissionType::Notifications));
    fixture.tab.permissions()->answer(false);
    QCOMPARE(spy.count(), 3);
    QCOMPARE(fixture.stateOf(origin, PermissionType::Notifications), PermissionState::Denied);
    QVERIFY(!fixture.hasPending());
}

void TestSitePermissions::navigatingAwayDeniesPendingPermissions()
{
    PermissionFixture fixture;
    const QUrl origin(QStringLiteral("https://leave.example"));
    fixture.tab.setUrl(origin);
    fixture.enqueueGeolocation(origin);
    fixture.tab.setUrl(QUrl(QStringLiteral("https://other.example/")));
    QCOMPARE(fixture.geolocationState(origin), PermissionState::Denied);
    QVERIFY(!fixture.hasPending());
}

void TestSitePermissions::navigatingWithinSameOriginKeepsPendingPermissions()
{
    PermissionFixture fixture;
    const QUrl origin(QStringLiteral("https://stay.example"));
    fixture.tab.setUrl(QUrl(QStringLiteral("https://stay.example/meet")));
    fixture.enqueueGeolocation(origin);
    fixture.tab.setUrl(QUrl(QStringLiteral("https://stay.example/meet#room")));
    QVERIFY(fixture.hasPending());
    fixture.tab.setUrl(QUrl(QStringLiteral("https://stay.example/meet/room")));
    QVERIFY(fixture.hasPending());
    QCOMPARE(fixture.geolocationState(origin), PermissionState::Ask);
}

void TestSitePermissions::navigatingToAnotherOriginDeniesPendingPermissions()
{
    PermissionFixture fixture;
    const QUrl origin(QStringLiteral("https://stay.example"));
    fixture.tab.setUrl(QUrl(QStringLiteral("https://stay.example/meet")));
    fixture.enqueueGeolocation(origin);
    fixture.tab.setUrl(QUrl(QStringLiteral("https://elsewhere.example/")));
    QCOMPARE(fixture.geolocationState(origin), PermissionState::Denied);
    QVERIFY(!fixture.hasPending());
}

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();
    QTemporaryDir home;
    if (!useIsolatedHome(home))
        return 1;
    QGuiApplication app(argc, argv);
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));
    TestSitePermissions test;
    const int queueFailures = QTest::qExec(&test, argc, argv);
    return queueFailures + runTestSitePermissionsUi(argc, argv);
}

#include "tst_sitepermissions.moc"
