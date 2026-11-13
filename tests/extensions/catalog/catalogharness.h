#pragma once

#include <optional>

#include "core/settings/settings.h"
#include "../extensionsharness.h"

struct CatalogFixture {
    QString root;
    QString version;
    QStringList permissions;
    QString checksum;
    qint64 size = -1;
    std::optional<QStringList> catalogPermissions;
};

inline CatalogFixture catalogFixture(const QString &root, const QString &version,
                                     const QStringList &permissions)
{
    CatalogFixture fixture;
    fixture.root = root;
    fixture.version = version;
    fixture.permissions = permissions;
    return fixture;
}

inline QString packCatalogPackage(const CatalogFixture &fixture)
{
    const QString dir = makeVariant(fixture.root, QStringLiteral("pkg-") + fixture.version, [&](QJsonObject &manifest) {
        manifest.insert(QStringLiteral("version"), fixture.version);
        manifest.insert(QStringLiteral("permissions"), QJsonArray::fromStringList(fixture.permissions));
    });
    const QString zip = fixture.root + QStringLiteral("/packages/sample-%1.kondorext").arg(fixture.version);
    QDir().mkpath(fixture.root + QStringLiteral("/packages"));
    zipDirectory(dir, zip);
    return zip;
}

inline QJsonObject catalogEntry(const CatalogFixture &fixture, const QString &zip)
{
    const QStringList advertised = fixture.catalogPermissions.value_or(fixture.permissions);
    return {
        {QStringLiteral("id"), QStringLiteral("sample")},
        {QStringLiteral("name"), QStringLiteral("Sample Extension")},
        {QStringLiteral("name[pt_BR]"), QStringLiteral("Extensão de Exemplo")},
        {QStringLiteral("description"), QStringLiteral("Marks pages.")},
        {QStringLiteral("version"), fixture.version},
        {QStringLiteral("author"), QStringLiteral("Kondor contributors")},
        {QStringLiteral("icon"), QStringLiteral("weather-clear-night")},
        {QStringLiteral("permissions"), QJsonArray::fromStringList(advertised)},
        {QStringLiteral("matches"), QJsonArray{QStringLiteral("*://127.0.0.1/*"), QStringLiteral("*://localhost/*")}},
        {QStringLiteral("package"), QStringLiteral("packages/sample-%1.kondorext").arg(fixture.version)},
        {QStringLiteral("sha256"), fixture.checksum.isEmpty() ? sha256Of(zip) : fixture.checksum},
        {QStringLiteral("size"), fixture.size >= 0 ? fixture.size : QFileInfo(zip).size()},
    };
}

inline QUrl writeCatalog(const CatalogFixture &fixture)
{
    const QJsonObject entry = catalogEntry(fixture, packCatalogPackage(fixture));
    const QJsonObject catalog{{QStringLiteral("version"), 1},
                              {QStringLiteral("generated"), QStringLiteral("2026-11-10T21:00:00Z")},
                              {QStringLiteral("extensions"), QJsonArray{entry}}};
    const QString file = fixture.root + QStringLiteral("/catalog.json");
    writeFile(file, QJsonDocument(catalog).toJson());
    return QUrl::fromLocalFile(file);
}

inline bool refreshCatalog(ExtensionCatalog *catalog, const QUrl &url)
{
    catalog->setCatalogUrl(url);
    QSignalSpy states(catalog, &ExtensionCatalog::stateChanged);
    catalog->refresh();
    const auto isDone = [&]() {
        return catalog->state() == QLatin1String("ready") || catalog->state() == QLatin1String("error");
    };
    return QTest::qWaitFor(isDone, 10000) && catalog->state() == QLatin1String("ready");
}

inline void verifyRefreshed(const QUrl &url)
{
    QVERIFY(refreshCatalog(ExtensionCatalog::instance(), url));
}

inline void verifyPendingInstallAppears()
{
    ExtensionManager *manager = ExtensionManager::instance();
    QVERIFY(QTest::qWaitFor([&]() { return !manager->pendingInstall().isEmpty(); }, 10000));
}

inline void verifyInstalledFromCatalog(const CatalogFixture &fixture)
{
    verifyRefreshed(writeCatalog(fixture));
    ExtensionCatalog::instance()->install(QStringLiteral("sample"));
    verifyPendingInstallAppears();
    ExtensionManager::instance()->confirmInstall();
    QCOMPARE(ExtensionManager::instance()->installedVersion(QStringLiteral("sample")), fixture.version);
}

inline bool isUpdateWaitingForReview()
{
    ExtensionManager *manager = ExtensionManager::instance();
    return manager->data(manager->index(0), ExtensionManager::UpdateNeedsReviewRole).toBool();
}

inline QString installedSampleVersion()
{
    return ExtensionManager::instance()->installedVersion(QStringLiteral("sample"));
}
