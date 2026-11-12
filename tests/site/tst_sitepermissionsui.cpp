#include "sitepermissionsharness.h"

class TestSitePermissionsUi : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void requestBarShowsThePendingPermission();
    void answeringTheRequestBarGrantsAndHidesIt();
    void dialogListsDecisions();
    void dialogRevokesDecisions();

private:
    QQmlEngine m_engine;
};

void TestSitePermissionsUi::initTestCase()
{
    registerSitePermissionTypes();
}

void TestSitePermissionsUi::requestBarShowsThePendingPermission()
{
    PermissionFixture fixture;
    fixture.enqueueGeolocation(QUrl(QStringLiteral("https://meet.example")));
    QScopedPointer<QObject> bar(loadPermissionBar(m_engine, &fixture.tab));
    QVERIFY2(bar, "the permission bar must load");
    QCOMPARE(bar->property("visible").toBool(), true);
    QObject *text = findByClassName(bar.data(), QStringLiteral("Label"));
    QVERIFY(text);
    QVERIFY(text->property("text").toString().contains(QStringLiteral("meet.example")));
    QVERIFY(text->property("text").toString().contains(QStringLiteral("location")));
}

void TestSitePermissionsUi::answeringTheRequestBarGrantsAndHidesIt()
{
    PermissionFixture fixture;
    const QUrl origin(QStringLiteral("https://meet.example"));
    fixture.enqueueGeolocation(origin);
    QScopedPointer<QObject> bar(loadPermissionBar(m_engine, &fixture.tab));
    QVERIFY2(bar, "the permission bar must load");
    fixture.tab.permissions()->answer(true);
    QCOMPARE(bar->property("visible").toBool(), false);
    QCOMPARE(fixture.geolocationState(origin), PermissionState::Granted);
}

void TestSitePermissionsUi::dialogListsDecisions()
{
    grantGeolocation(QUrl(QStringLiteral("https://permissions.example")));
    QScopedPointer<QQuickWindow> window(loadSitePermissionsWindow(m_engine));
    QVERIFY2(window, "the Site Permissions window must load");
    QVERIFY(window->isVisible());
    const QVariantList rows = window->property("rows").toList();
    QCOMPARE(rows.size(), 1);
    const QVariantMap row = rows.first().toMap();
    QCOMPARE(row.value(QStringLiteral("site")).toString(), QStringLiteral("permissions.example"));
    QCOMPARE(row.value(QStringLiteral("perm")).toString(), QStringLiteral("Location"));
    QCOMPARE(row.value(QStringLiteral("granted")).toBool(), true);
}

void TestSitePermissionsUi::dialogRevokesDecisions()
{
    const QUrl origin(QStringLiteral("https://permissions.example"));
    grantGeolocation(origin);
    QScopedPointer<QQuickWindow> window(loadSitePermissionsWindow(m_engine));
    QVERIFY2(window, "the Site Permissions window must load");
    const QVariant permission = window->property("rows").toList().first().toMap().value(QStringLiteral("permission"));
    QVERIFY(permission.value<QWebEnginePermission>().isValid());
    QMetaObject::invokeMethod(window.data(), "revoke", Q_ARG(QVariant, permission));
    QCOMPARE(window->property("rows").toList().size(), 0);
    QCOMPARE(ProfileManager::instance()->defaultProfile()->queryPermission(origin, PermissionType::Geolocation).state(),
             PermissionState::Ask);
}

int runTestSitePermissionsUi(int argc, char *argv[])
{
    TestSitePermissionsUi test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_sitepermissionsui.moc"
