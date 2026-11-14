#include <QDir>
#include <QFile>
#include <QStandardPaths>
#include <QTemporaryDir>
#include <QTest>

#include "core/installedicons.h"

class TestInstalledIcons : public QObject
{
    Q_OBJECT

private slots:
    void findsIconInDataDirectory();
    void missesIconOutsideDataDirectories();

private:
    static constexpr const char *iconName = "kondor-sample-symbolic";
    QString iconFolder(const QString &dataDirectory) const;
};

QString TestInstalledIcons::iconFolder(const QString &dataDirectory) const
{
    return dataDirectory + QStringLiteral("/icons/hicolor/scalable/actions");
}

void TestInstalledIcons::findsIconInDataDirectory()
{
    QTemporaryDir dataDirectory;
    QVERIFY(QDir().mkpath(iconFolder(dataDirectory.path())));
    QFile icon(iconFolder(dataDirectory.path()) + QStringLiteral("/") + QLatin1String(iconName) + QStringLiteral(".svg"));
    QVERIFY(icon.open(QIODevice::WriteOnly));
    qputenv("XDG_DATA_DIRS", dataDirectory.path().toUtf8());
    QVERIFY(InstalledIcons::instance()->isInstalled(QLatin1String(iconName)));
}

void TestInstalledIcons::missesIconOutsideDataDirectories()
{
    QTemporaryDir dataDirectory;
    qputenv("XDG_DATA_DIRS", dataDirectory.path().toUtf8());
    QVERIFY(!InstalledIcons::instance()->isInstalled(QLatin1String(iconName)));
}

QTEST_GUILESS_MAIN(TestInstalledIcons)
#include "tst_installedicons.moc"
