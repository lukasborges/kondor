#include <QTest>
#include <type_traits>

#include "adblock/adblockmanager.h"
#include "app/aboutinfo.h"
#include "app/startupargs.h"
#include "app/windowmanager.h"
#include "bookmarks/bookmarkmanager.h"
#include "browser/faviconstore.h"
#include "browser/profilemanager.h"
#include "browser/searchsuggestions.h"
#include "browser/sessionmanager.h"
#include "browser/zoommanager.h"
#include "core/filehelper.h"
#include "core/notifier.h"
#include "core/settings.h"
#include "downloads/downloadmanager.h"
#include "extensions/extensioncatalog.h"
#include "extensions/extensionmanager.h"
#include "history/historymanager.h"
#include "passwords/passwordstore.h"

#define ASSERT_QML_CALLS_CREATE(Type)                                           \
    static_assert(!std::is_default_constructible_v<Type>,                       \
                  "QML would build its own instance instead of calling create()")

ASSERT_QML_CALLS_CREATE(AdBlockManager);
ASSERT_QML_CALLS_CREATE(AboutInfo);
ASSERT_QML_CALLS_CREATE(StartupArgs);
ASSERT_QML_CALLS_CREATE(WindowManager);
ASSERT_QML_CALLS_CREATE(BookmarkManager);
ASSERT_QML_CALLS_CREATE(FaviconStore);
ASSERT_QML_CALLS_CREATE(ProfileManager);
ASSERT_QML_CALLS_CREATE(SearchSuggestions);
ASSERT_QML_CALLS_CREATE(SessionManager);
ASSERT_QML_CALLS_CREATE(ZoomManager);
ASSERT_QML_CALLS_CREATE(FileHelper);
ASSERT_QML_CALLS_CREATE(Notifier);
ASSERT_QML_CALLS_CREATE(Settings);
ASSERT_QML_CALLS_CREATE(DownloadManager);
ASSERT_QML_CALLS_CREATE(ExtensionCatalog);
ASSERT_QML_CALLS_CREATE(ExtensionManager);
ASSERT_QML_CALLS_CREATE(HistoryManager);
ASSERT_QML_CALLS_CREATE(PasswordStore);

class TestSingletons : public QObject
{
    Q_OBJECT
};

QTEST_GUILESS_MAIN(TestSingletons)
#include "tst_singletons.moc"
