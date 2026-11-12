set(KONDOR_DATABASE_SOURCES
    ${CMAKE_SOURCE_DIR}/src/core/database.h
    ${CMAKE_SOURCE_DIR}/src/core/database.cpp
    ${CMAKE_SOURCE_DIR}/src/core/databasemigrations.h
    ${CMAKE_SOURCE_DIR}/src/core/databasemigrations.cpp
    ${CMAKE_SOURCE_DIR}/src/core/defaultbookmarks.h
    ${CMAKE_SOURCE_DIR}/src/core/defaultbookmarks.cpp
    ${CMAKE_SOURCE_DIR}/src/core/sql.h
    ${CMAKE_SOURCE_DIR}/src/core/sql.cpp
)

set(KONDOR_SETTINGS_SOURCES
    ${CMAKE_SOURCE_DIR}/src/core/settings.h
    ${CMAKE_SOURCE_DIR}/src/core/settings.cpp
    ${CMAKE_SOURCE_DIR}/src/core/settingsdefaults.h
    ${CMAKE_SOURCE_DIR}/src/core/settingsdefaults.cpp
    ${CMAKE_SOURCE_DIR}/src/core/spellcheckdictionaries.h
    ${CMAKE_SOURCE_DIR}/src/core/spellcheckdictionaries.cpp
    ${CMAKE_SOURCE_DIR}/src/core/searchengines.h
    ${CMAKE_SOURCE_DIR}/src/core/searchengines.cpp
)

set(KONDOR_NOTIFIER_SOURCES
    ${CMAKE_SOURCE_DIR}/src/core/notifier.h
    ${CMAKE_SOURCE_DIR}/src/core/notifier.cpp
)

set(KONDOR_BOOKMARK_MANAGER_SOURCES
    ${CMAKE_SOURCE_DIR}/src/bookmarks/bookmarkmanager.h
    ${CMAKE_SOURCE_DIR}/src/bookmarks/bookmarkmanager.cpp
    ${CMAKE_SOURCE_DIR}/src/bookmarks/bookmarkqueries.h
    ${CMAKE_SOURCE_DIR}/src/bookmarks/bookmarkqueries.cpp
    ${CMAKE_SOURCE_DIR}/src/bookmarks/bookmarkfoldertree.h
    ${CMAKE_SOURCE_DIR}/src/bookmarks/bookmarkfoldertree.cpp
    ${CMAKE_SOURCE_DIR}/src/bookmarks/bookmarkhtmlparser.h
    ${CMAKE_SOURCE_DIR}/src/bookmarks/bookmarkhtmlparser.cpp
    ${CMAKE_SOURCE_DIR}/src/bookmarks/bookmarkhtmlimporter.h
    ${CMAKE_SOURCE_DIR}/src/bookmarks/bookmarkhtmlimporter.cpp
    ${CMAKE_SOURCE_DIR}/src/bookmarks/bookmarkhtmltext.h
    ${CMAKE_SOURCE_DIR}/src/bookmarks/bookmarkhtmltext.cpp
    ${CMAKE_SOURCE_DIR}/src/bookmarks/bookmarkchecks.h
    ${CMAKE_SOURCE_DIR}/src/bookmarks/bookmarkchecks.cpp
)

set(KONDOR_BOOKMARK_MODEL_SOURCES
    ${CMAKE_SOURCE_DIR}/src/bookmarks/bookmarkmodel.h
    ${CMAKE_SOURCE_DIR}/src/bookmarks/bookmarkmodel.cpp
)

set(KONDOR_HISTORY_MANAGER_SOURCES
    ${CMAKE_SOURCE_DIR}/src/history/historymanager.h
    ${CMAKE_SOURCE_DIR}/src/history/historymanager.cpp
    ${CMAKE_SOURCE_DIR}/src/history/historysearch.h
    ${CMAKE_SOURCE_DIR}/src/history/historysearch.cpp
    ${CMAKE_SOURCE_DIR}/src/history/topsitesranking.h
    ${CMAKE_SOURCE_DIR}/src/history/topsitesranking.cpp
)

set(KONDOR_HISTORY_MODEL_SOURCES
    ${CMAKE_SOURCE_DIR}/src/history/historymodel.h
    ${CMAKE_SOURCE_DIR}/src/history/historymodel.cpp
)

set(KONDOR_DOWNLOAD_MANAGER_SOURCES
    ${CMAKE_SOURCE_DIR}/src/downloads/downloadmanager.h
    ${CMAKE_SOURCE_DIR}/src/downloads/downloadmanager.cpp
    ${CMAKE_SOURCE_DIR}/src/downloads/downloadmodel.h
    ${CMAKE_SOURCE_DIR}/src/downloads/downloadmodel.cpp
    ${CMAKE_SOURCE_DIR}/src/downloads/downloadroles.h
    ${CMAKE_SOURCE_DIR}/src/downloads/downloadroles.cpp
    ${CMAKE_SOURCE_DIR}/src/downloads/transferspeed.h
    ${CMAKE_SOURCE_DIR}/src/downloads/transferspeed.cpp
)

set(KONDOR_TAB_SOURCES
    ${CMAKE_SOURCE_DIR}/src/browser/assignandnotify.h
    ${CMAKE_SOURCE_DIR}/src/browser/tab.h
    ${CMAKE_SOURCE_DIR}/src/browser/tab.cpp
    ${CMAKE_SOURCE_DIR}/src/browser/tabcommands.cpp
    ${CMAKE_SOURCE_DIR}/src/browser/tabsecurity.h
    ${CMAKE_SOURCE_DIR}/src/browser/tabsecurity.cpp
    ${CMAKE_SOURCE_DIR}/src/browser/tabpermissions.h
    ${CMAKE_SOURCE_DIR}/src/browser/tabpermissions.cpp
    ${CMAKE_SOURCE_DIR}/src/browser/tabpasswords.h
    ${CMAKE_SOURCE_DIR}/src/browser/tabpasswords.cpp
    ${CMAKE_SOURCE_DIR}/src/browser/tabextensionitems.h
    ${CMAKE_SOURCE_DIR}/src/browser/tabextensionitems.cpp
)

set(KONDOR_TAB_MODEL_SOURCES
    ${CMAKE_SOURCE_DIR}/src/browser/tabmodel.h
    ${CMAKE_SOURCE_DIR}/src/browser/tabmodel.cpp
    ${CMAKE_SOURCE_DIR}/src/browser/tabmodelclosing.cpp
    ${CMAKE_SOURCE_DIR}/src/browser/closedtabs.h
    ${CMAKE_SOURCE_DIR}/src/browser/closedtabs.cpp
)

set(KONDOR_PROFILE_MANAGER_SOURCES
    ${CMAKE_SOURCE_DIR}/src/browser/profilemanager.h
    ${CMAKE_SOURCE_DIR}/src/browser/profilemanager.cpp
    ${CMAKE_SOURCE_DIR}/src/browser/profilesetup.h
    ${CMAKE_SOURCE_DIR}/src/browser/profilesetup.cpp
    ${CMAKE_SOURCE_DIR}/src/browser/pagescripts.h
    ${CMAKE_SOURCE_DIR}/src/browser/pagescripts.cpp
    ${CMAKE_SOURCE_DIR}/src/browser/certificateoverrides.h
    ${CMAKE_SOURCE_DIR}/src/browser/certificateoverrides.cpp
)

set(KONDOR_SESSION_SOURCES
    ${CMAKE_SOURCE_DIR}/src/browser/sessionwindow.h
    ${CMAKE_SOURCE_DIR}/src/browser/sessionformat.h
    ${CMAKE_SOURCE_DIR}/src/browser/sessionformat.cpp
    ${CMAKE_SOURCE_DIR}/src/browser/sessionmanager.h
    ${CMAKE_SOURCE_DIR}/src/browser/sessionmanager.cpp
)

set(KONDOR_SUGGESTION_SOURCES
    ${CMAKE_SOURCE_DIR}/src/browser/suggestionlist.h
    ${CMAKE_SOURCE_DIR}/src/browser/suggestionlist.cpp
    ${CMAKE_SOURCE_DIR}/src/browser/searchsuggestions.h
    ${CMAKE_SOURCE_DIR}/src/browser/searchsuggestions.cpp
)

set(KONDOR_FILTER_ENGINE_SOURCES
    ${CMAKE_SOURCE_DIR}/src/adblock/filterengine.h
    ${CMAKE_SOURCE_DIR}/src/adblock/filterengine.cpp
    ${CMAKE_SOURCE_DIR}/src/adblock/filterrule.h
    ${CMAKE_SOURCE_DIR}/src/adblock/filterrule.cpp
    ${CMAKE_SOURCE_DIR}/src/adblock/filteroptions.h
    ${CMAKE_SOURCE_DIR}/src/adblock/filteroptions.cpp
    ${CMAKE_SOURCE_DIR}/src/adblock/filterpattern.h
    ${CMAKE_SOURCE_DIR}/src/adblock/filterpattern.cpp
    ${CMAKE_SOURCE_DIR}/src/adblock/filterrequest.h
)

set(KONDOR_ADBLOCK_SOURCES
    ${KONDOR_FILTER_ENGINE_SOURCES}
    ${CMAKE_SOURCE_DIR}/src/adblock/adblockinterceptor.h
    ${CMAKE_SOURCE_DIR}/src/adblock/adblockinterceptor.cpp
    ${CMAKE_SOURCE_DIR}/src/adblock/adblockallowlist.h
    ${CMAKE_SOURCE_DIR}/src/adblock/adblockallowlist.cpp
    ${CMAKE_SOURCE_DIR}/src/adblock/filterlists.h
    ${CMAKE_SOURCE_DIR}/src/adblock/filterlists.cpp
    ${CMAKE_SOURCE_DIR}/src/adblock/filterlistdownloader.h
    ${CMAKE_SOURCE_DIR}/src/adblock/filterlistdownloader.cpp
    ${CMAKE_SOURCE_DIR}/src/adblock/adblockmanager.h
    ${CMAKE_SOURCE_DIR}/src/adblock/adblockmanager.cpp
)
