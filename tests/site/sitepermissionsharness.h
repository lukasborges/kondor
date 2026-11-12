#pragma once

#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickWebEngineProfile>
#include <QQuickWindow>
#include <QTest>
#include <QWebEnginePermission>

#include "browser/profilemanager.h"
#include "browser/tab.h"
#include "common/qmltesthelpers.h"

using PermissionType = QWebEnginePermission::PermissionType;
using PermissionState = QWebEnginePermission::State;

inline void registerSitePermissionTypes()
{
    static const bool typesRegistered = [] {
        registerSingleton<ProfileManager>("ProfileManager");
        qmlRegisterUncreatableType<Tab>("Kondor", 1, 0, "Tab", QStringLiteral("Tabs are created by TabModel"));
        return true;
    }();
    Q_UNUSED(typesRegistered)
}

struct MemoryProfile
{
    MemoryProfile()
    {
        profile.setPersistentPermissionsPolicy(
                QQuickWebEngineProfile::PersistentPermissionsPolicy::StoreInMemory);
    }

    QQuickWebEngineProfile profile;
};

struct PermissionFixture : MemoryProfile
{
    Tab tab{&profile};

    QWebEnginePermission query(const QUrl &origin, PermissionType type)
    {
        return profile.queryPermission(origin, type);
    }

    PermissionState stateOf(const QUrl &origin, PermissionType type)
    {
        return query(origin, type).state();
    }

    PermissionState geolocationState(const QUrl &origin)
    {
        return stateOf(origin, PermissionType::Geolocation);
    }

    void enqueue(const QUrl &origin, PermissionType type)
    {
        tab.permissions()->enqueue(query(origin, type));
    }

    void enqueueGeolocation(const QUrl &origin) { enqueue(origin, PermissionType::Geolocation); }
    bool hasPending() const { return tab.permissions()->pending().isValid(); }

    int pendingType() const
    {
        return int(tab.permissions()->pending().value<QWebEnginePermission>().permissionType());
    }
};

inline QObject *loadKondorQml(QQmlEngine &engine, const QString &file, const QVariantMap &properties = {})
{
    engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));
    QQmlComponent component(&engine, QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR "/") + file));
    QObject *object = component.createWithInitialProperties(properties);
    if (!object)
        qWarning() << component.errors();
    return object;
}

inline QObject *loadPermissionBar(QQmlEngine &engine, Tab *tab)
{
    return loadKondorQml(engine, QStringLiteral("site/PermissionBar.qml"),
                         { { QStringLiteral("tab"), QVariant::fromValue(tab) } });
}

inline QQuickWindow *loadSitePermissionsWindow(QQmlEngine &engine)
{
    auto *window = qobject_cast<QQuickWindow *>(
            loadKondorQml(engine, QStringLiteral("site/SitePermissionsDialog.qml")));
    if (window)
        QMetaObject::invokeMethod(window, "showWindow");
    return window;
}

inline void grantGeolocation(const QUrl &origin)
{
    ProfileManager::instance()->defaultProfile()->queryPermission(origin, PermissionType::Geolocation).grant();
}

int runTestSitePermissionsUi(int argc, char *argv[]);
