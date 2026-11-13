#include <QCoreApplication>
#include <QTemporaryDir>

#include "bookmarksprofileharness.h"
#include "../common/isolatedhome.h"
#include "core/database/database.h"

namespace {
int migrateProfileInChildMode(const char *dataHome)
{
    qputenv("XDG_DATA_HOME", dataHome);
    return Database::instance()->isValid() ? 0 : 1;
}

bool isMigrateChildMode(int argc, char *argv[])
{
    return argc >= 3 && qstrcmp(argv[1], "--migrate") == 0;
}
}

int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE-Test"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor-Bookmarks-Test"));
    if (isMigrateChildMode(argc, argv))
        return migrateProfileInChildMode(argv[2]);
    QTemporaryDir dataDir;
    if (!useIsolatedHome(dataDir))
        return 1;
    int failures = runTestDefaultBookmarks(argc, argv);
    failures += runTestBookmarkTree(argc, argv);
    failures += runTestBookmarkImport(argc, argv);
    return failures;
}
