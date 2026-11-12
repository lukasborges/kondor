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
