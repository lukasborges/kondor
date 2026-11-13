set(KONDOR_TEST_QML_IMPORT_DIR "${CMAKE_CURRENT_BINARY_DIR}/qmlimport")
file(GLOB_RECURSE KONDOR_QML_SOURCES "${CMAKE_SOURCE_DIR}/qml/*.qml")
set(KONDOR_QMLDIR_CONTENT "module Kondor\n")
foreach(qml_file IN LISTS KONDOR_QML_SOURCES)
    get_filename_component(qml_type "${qml_file}" NAME_WE)
    file(RELATIVE_PATH qml_relative "${KONDOR_TEST_QML_IMPORT_DIR}/Kondor" "${qml_file}")
    string(APPEND KONDOR_QMLDIR_CONTENT "${qml_type} 1.0 ${qml_relative}\n")
endforeach()
file(WRITE "${KONDOR_TEST_QML_IMPORT_DIR}/Kondor/qmldir" "${KONDOR_QMLDIR_CONTENT}")

qt_add_library(kondor_testlib STATIC
    ${KONDOR_ADBLOCK_SOURCES}
    ${KONDOR_BOOKMARK_MANAGER_SOURCES}
    ${KONDOR_BOOKMARK_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_EXTENSION_BRIDGE_SOURCES}
    ${KONDOR_EXTENSION_MANAGER_SOURCES}
    ${KONDOR_EXTENSION_PACKAGE_SOURCES}
    ${KONDOR_FILTER_ENGINE_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_SESSION_SOURCES}
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_SUGGESTION_SOURCES}
    ${KONDOR_TAB_MODEL_SOURCES}
    ${KONDOR_TAB_SOURCES}
    ${CMAKE_SOURCE_DIR}/src/app/aboutinfo.cpp
    ${CMAKE_SOURCE_DIR}/src/app/commandline/extensionpackages.cpp
    ${CMAKE_SOURCE_DIR}/src/app/commandline/startupurl.cpp
    ${CMAKE_SOURCE_DIR}/src/app/instance/singleinstance.cpp
    ${CMAKE_SOURCE_DIR}/src/app/instance/singleinstancemessage.cpp
    ${CMAKE_SOURCE_DIR}/src/browser/address/addressresolver.cpp
    ${CMAKE_SOURCE_DIR}/src/browser/address/suggestionlist.cpp
    ${CMAKE_SOURCE_DIR}/src/browser/favicons/faviconstore.cpp
    ${CMAKE_SOURCE_DIR}/src/browser/zoommanager.cpp
    ${CMAKE_SOURCE_DIR}/src/core/filehelper.cpp
    ${CMAKE_SOURCE_DIR}/src/downloads/transferspeed.cpp
    ${CMAKE_SOURCE_DIR}/src/extensions/catalog/catalogentry.cpp
    ${CMAKE_SOURCE_DIR}/src/extensions/install/extensionloader.cpp
    ${CMAKE_SOURCE_DIR}/src/extensions/package/packagesuffix.cpp
    ${CMAKE_SOURCE_DIR}/src/extensions/scripts/contentscriptbuilder.cpp
    ${CMAKE_SOURCE_DIR}/src/extensions/state/extensionsettings.cpp
    ${CMAKE_SOURCE_DIR}/src/extensions/state/extensionstorage.cpp
    ${CMAKE_SOURCE_DIR}/src/passwords/csv/csvreader.cpp
    ${CMAKE_SOURCE_DIR}/src/passwords/csv/passwordimport.cpp
    ${CMAKE_SOURCE_DIR}/src/passwords/csv/passwordimportcolumns.cpp
    ${CMAKE_SOURCE_DIR}/src/passwords/csv/passwordimportfile.cpp
    ${CMAKE_SOURCE_DIR}/src/passwords/csv/passwordimportplan.cpp
    ${CMAKE_SOURCE_DIR}/src/passwords/import/importcommit.cpp
    ${CMAKE_SOURCE_DIR}/src/passwords/import/importinfo.cpp
    ${CMAKE_SOURCE_DIR}/src/passwords/import/importoutcome.cpp
    ${CMAKE_SOURCE_DIR}/src/passwords/import/importpreparation.cpp
    ${CMAKE_SOURCE_DIR}/src/passwords/passwordorigin.cpp
)

set_target_properties(kondor_testlib PROPERTIES AUTOMOC ON)

target_include_directories(kondor_testlib PUBLIC
    ${CMAKE_SOURCE_DIR}/src
)

target_link_libraries(kondor_testlib PRIVATE
    Qt6::Concurrent
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Network
    Qt6::Qml
    Qt6::Quick
    Qt6::Sql
    Qt6::WebChannel
    Qt6::WebEngineCore
    Qt6::WebEngineQuick
    Qt6::Widgets
    KF6::Wallet
    KF6::Archive
)

qt_add_executable(tst_addressresolver
    browser/address/tst_addressresolver.cpp
)

target_include_directories(tst_addressresolver PRIVATE
    ../src
)

target_link_libraries(tst_addressresolver PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_addressresolver COMMAND tst_addressresolver)

qt_add_executable(tst_startupurl
    app/tst_startupurl.cpp
)

target_include_directories(tst_startupurl PRIVATE
    ../src
)

target_link_libraries(tst_startupurl PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_startupurl COMMAND tst_startupurl)

qt_add_executable(tst_tabmodel
    browser/tabs/tst_tabmodel.cpp
    browser/tabs/tst_recentlyclosedtabs.cpp
    browser/tabs/tst_tabnewtabpage.cpp
    browser/tabs/tst_tabpinning.cpp
)

target_include_directories(tst_tabmodel PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_tabmodel PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
    Qt6::Concurrent
)

add_test(NAME tst_tabmodel COMMAND tst_tabmodel)
set_tests_properties(tst_tabmodel PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_tabpasswords
    browser/tabs/tst_tabpasswords.cpp
)

target_include_directories(tst_tabpasswords PRIVATE
    ../src
)

target_link_libraries(tst_tabpasswords PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
    Qt6::Concurrent
)

add_test(NAME tst_tabpasswords COMMAND tst_tabpasswords)
set_tests_properties(tst_tabpasswords PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_tabsecurity
    browser/tabs/tst_tabsecurity.cpp
)

target_include_directories(tst_tabsecurity PRIVATE
    ../src
)

target_link_libraries(tst_tabsecurity PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
    Qt6::Concurrent
)

add_test(NAME tst_tabsecurity COMMAND tst_tabsecurity)
set_tests_properties(tst_tabsecurity PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_addresssuggestions
    browser/address/tst_addresssuggestions.cpp
)

target_compile_definitions(tst_addresssuggestions PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_addresssuggestions PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_addresssuggestions PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
    Qt6::Concurrent
)

add_test(NAME tst_addresssuggestions COMMAND tst_addresssuggestions)
set_tests_properties(tst_addresssuggestions PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_addressbar
    browser/address/tst_addressbar.cpp
)

target_compile_definitions(tst_addressbar PRIVATE
    KONDOR_TEST_DATA_DIR="${CMAKE_CURRENT_SOURCE_DIR}/data"
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_addressbar PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_addressbar PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
    Qt6::Concurrent
)

add_test(NAME tst_addressbar COMMAND tst_addressbar)
set_tests_properties(tst_addressbar PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_bookmarks
    bookmarks/tst_bookmarks.cpp
    bookmarks/tst_defaultbookmarks.cpp
    bookmarks/tst_bookmarktree.cpp
    bookmarks/import/tst_bookmarkimport.cpp
)

target_include_directories(tst_bookmarks PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_bookmarks PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Sql
    Qt6::Test
)

add_test(NAME tst_bookmarks COMMAND tst_bookmarks)
set_tests_properties(tst_bookmarks PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen"
)

qt_add_executable(tst_bookmarkswindow
    bookmarks/tst_bookmarkswindow.cpp
    bookmarks/tst_bookmarkswindowdrag.cpp
)

target_compile_definitions(tst_bookmarkswindow PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_bookmarkswindow PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_bookmarkswindow PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
    Qt6::Concurrent
)

add_test(NAME tst_bookmarkswindow COMMAND tst_bookmarkswindow)
set_tests_properties(tst_bookmarkswindow PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_mainmenu
    app/tst_mainmenu.cpp
)

target_compile_definitions(tst_mainmenu PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_mainmenu PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_mainmenu PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
    Qt6::Concurrent
)

add_test(NAME tst_mainmenu COMMAND tst_mainmenu)
set_tests_properties(tst_mainmenu PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_toolbaraccessibility
    app/tst_toolbaraccessibility.cpp
)

target_compile_definitions(tst_toolbaraccessibility PRIVATE
    KONDOR_TEST_DATA_DIR="${CMAKE_CURRENT_SOURCE_DIR}/data"
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_toolbaraccessibility PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_toolbaraccessibility PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
    Qt6::Concurrent
)

add_test(NAME tst_toolbaraccessibility COMMAND tst_toolbaraccessibility)
set_tests_properties(tst_toolbaraccessibility PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_topsites
    history/tst_topsites.cpp
    history/tst_historysuggestions.cpp
)

target_include_directories(tst_topsites PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_topsites PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::Sql
    Qt6::Test
)

add_test(NAME tst_topsites COMMAND tst_topsites)

qt_add_executable(tst_faviconstore
    browser/tst_faviconstore.cpp
)

target_include_directories(tst_faviconstore PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_faviconstore PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::Sql
    Qt6::Test
)

add_test(NAME tst_faviconstore COMMAND tst_faviconstore)

qt_add_executable(tst_aboutinfo
    app/tst_aboutinfo.cpp
)

qt_add_resources(tst_aboutinfo "license"
    PREFIX "/"
    FILES
        ../LICENSE
)

target_compile_definitions(tst_aboutinfo PRIVATE
    PROJECT_VERSION="${PROJECT_VERSION}"
)

target_include_directories(tst_aboutinfo PRIVATE
    ../src
)

target_link_libraries(tst_aboutinfo PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Test
    Qt6::WebEngineCore
)

add_test(NAME tst_aboutinfo COMMAND tst_aboutinfo)
set_tests_properties(tst_aboutinfo PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen"
)

qt_add_executable(tst_singletons
    core/tst_singletons.cpp
)

target_include_directories(tst_singletons PRIVATE
    ../src
)

target_link_libraries(tst_singletons PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Network
    Qt6::Qml
    Qt6::Quick
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
    KF6::Archive
)

add_test(NAME tst_singletons COMMAND tst_singletons)

qt_add_executable(tst_settings
    core/tst_settings.cpp
)

target_include_directories(tst_settings PRIVATE
    ../src
)

target_link_libraries(tst_settings PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_settings COMMAND tst_settings)

qt_add_executable(tst_settingswindow
    settings/tst_settingswindow.cpp
    settings/tst_settingsapply.cpp
    settings/tst_settingsnavigation.cpp
)

target_compile_definitions(tst_settingswindow PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_settingswindow PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_settingswindow PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
    KF6::Archive
    Qt6::Concurrent
)

add_test(NAME tst_settingswindow COMMAND tst_settingswindow)
set_tests_properties(tst_settingswindow PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_tabstrip
    browser/tabstrip/tst_tabstrip.cpp
    browser/tabstrip/tst_tabstripwidths.cpp
    browser/tabstrip/tst_tabstripclosing.cpp
    browser/tabstrip/tst_tabdrag.cpp
    browser/tabstrip/tst_tabdragscroll.cpp
    browser/tabstrip/tst_tabdragrelease.cpp
    browser/tabstrip/tst_tabstripaccessibility.cpp
)

target_compile_definitions(tst_tabstrip PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_tabstrip PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_tabstrip PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
    Qt6::Concurrent
)

add_test(NAME tst_tabstrip COMMAND tst_tabstrip)
set_tests_properties(tst_tabstrip PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_tabstripscroll
    browser/tabstrip/tst_tabstripscroll.cpp
)

target_compile_definitions(tst_tabstripscroll PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_tabstripscroll PRIVATE
    ../src
)

target_link_libraries(tst_tabstripscroll PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
    Qt6::Concurrent
)

add_test(NAME tst_tabstripscroll COMMAND tst_tabstripscroll)
set_tests_properties(tst_tabstripscroll PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_sitepermissions
    site/tst_sitepermissions.cpp
    site/tst_sitepermissionsui.cpp
)

target_compile_definitions(tst_sitepermissions PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_sitepermissions PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_sitepermissions PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
    Qt6::Concurrent
)

add_test(NAME tst_sitepermissions COMMAND tst_sitepermissions)
set_tests_properties(tst_sitepermissions PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_pagecontextmenu
    browser/tst_pagecontextmenu.cpp
)

target_compile_definitions(tst_pagecontextmenu PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_pagecontextmenu PRIVATE
    ../src
)

target_link_libraries(tst_pagecontextmenu PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    Qt6::Concurrent
    Qt6::Network
    KF6::Wallet
)

add_test(NAME tst_pagecontextmenu COMMAND tst_pagecontextmenu)
set_tests_properties(tst_pagecontextmenu PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_permissiontypeinfo
    site/tst_permissiontypeinfo.cpp
)

target_compile_definitions(tst_permissiontypeinfo PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_permissiontypeinfo PRIVATE
    ../src
)

target_link_libraries(tst_permissiontypeinfo PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    Qt6::Concurrent
    Qt6::Network
    KF6::Wallet
)

add_test(NAME tst_permissiontypeinfo COMMAND tst_permissiontypeinfo)
set_tests_properties(tst_permissiontypeinfo PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_downloadstatus
    downloads/tst_downloadstatus.cpp
)

target_compile_definitions(tst_downloadstatus PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_downloadstatus PRIVATE
    ../src
)

target_link_libraries(tst_downloadstatus PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    Qt6::Concurrent
    Qt6::Network
    KF6::Wallet
)

add_test(NAME tst_downloadstatus COMMAND tst_downloadstatus)
set_tests_properties(tst_downloadstatus PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_sessionmanager
    browser/tst_sessionmanager.cpp
)

target_include_directories(tst_sessionmanager PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_sessionmanager PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
    Qt6::Concurrent
)

add_test(NAME tst_sessionmanager COMMAND tst_sessionmanager)
set_tests_properties(tst_sessionmanager PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_singleinstance
    app/tst_singleinstance.cpp
)

target_include_directories(tst_singleinstance PRIVATE
    ../src
)

target_link_libraries(tst_singleinstance PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Network
    Qt6::Test
)

add_test(NAME tst_singleinstance COMMAND tst_singleinstance)

qt_add_executable(tst_extensionpackages
    app/tst_extensionpackages.cpp
)

target_include_directories(tst_extensionpackages PRIVATE
    ../src
)

target_link_libraries(tst_extensionpackages PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_extensionpackages COMMAND tst_extensionpackages)

qt_add_executable(tst_filehelper
    core/tst_filehelper.cpp
)

target_include_directories(tst_filehelper PRIVATE
    ../src
)

target_link_libraries(tst_filehelper PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Test
)

add_test(NAME tst_filehelper COMMAND tst_filehelper)

qt_add_executable(tst_suggestionlist
    browser/address/tst_suggestionlist.cpp
)

target_include_directories(tst_suggestionlist PRIVATE
    ../src
)

target_link_libraries(tst_suggestionlist PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_suggestionlist COMMAND tst_suggestionlist)

qt_add_executable(tst_zoommanager
    browser/tst_zoommanager.cpp
)

target_include_directories(tst_zoommanager PRIVATE
    ../src
)

target_link_libraries(tst_zoommanager PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_zoommanager COMMAND tst_zoommanager)

# ProfileManager installs the ad blocker on every profile.
target_link_libraries(tst_tabmodel PRIVATE Qt6::Concurrent Qt6::Network)
target_link_libraries(tst_tabpasswords PRIVATE Qt6::Concurrent Qt6::Network)
target_link_libraries(tst_tabsecurity PRIVATE Qt6::Concurrent Qt6::Network)
target_link_libraries(tst_addresssuggestions PRIVATE Qt6::Concurrent Qt6::Network)
target_link_libraries(tst_addressbar PRIVATE Qt6::Concurrent Qt6::Network)
target_link_libraries(tst_bookmarkswindow PRIVATE Qt6::Concurrent Qt6::Network)
target_link_libraries(tst_mainmenu PRIVATE Qt6::Concurrent Qt6::Network)
target_link_libraries(tst_toolbaraccessibility PRIVATE Qt6::Concurrent Qt6::Network)
target_link_libraries(tst_settingswindow PRIVATE Qt6::Concurrent Qt6::Network)
target_link_libraries(tst_tabstrip PRIVATE Qt6::Concurrent Qt6::Network)
target_link_libraries(tst_tabstripscroll PRIVATE Qt6::Concurrent Qt6::Network)
target_link_libraries(tst_sitepermissions PRIVATE Qt6::Concurrent Qt6::Network)
target_link_libraries(tst_sessionmanager PRIVATE Qt6::Concurrent Qt6::Network)

qt_add_executable(tst_filterengine
    adblock/tst_filterengine.cpp
)

target_include_directories(tst_filterengine PRIVATE
    ../src
)

target_link_libraries(tst_filterengine PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_filterengine COMMAND tst_filterengine)

qt_add_executable(tst_adblockallowlist
    adblock/tst_adblockallowlist.cpp
)

target_include_directories(tst_adblockallowlist PRIVATE
    ../src
)

target_link_libraries(tst_adblockallowlist PRIVATE
    kondor_testlib
    Qt6::Concurrent
    Qt6::Core
    Qt6::Gui
    Qt6::Network
    Qt6::Qml
    Qt6::Test
    Qt6::WebEngineQuick
)

add_test(NAME tst_adblockallowlist COMMAND tst_adblockallowlist)
set_tests_properties(tst_adblockallowlist PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_passwordclipboard
    passwords/tst_passwordclipboard.cpp
    ${CMAKE_SOURCE_DIR}/src/passwords/passwordclipboard.cpp
)

target_include_directories(tst_passwordclipboard PRIVATE
    ../src
)

target_link_libraries(tst_passwordclipboard PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Test
)

add_test(NAME tst_passwordclipboard COMMAND tst_passwordclipboard)
set_tests_properties(tst_passwordclipboard PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen"
)

qt_add_executable(tst_passwordstore
    passwords/tst_passwordstore.cpp
)

target_include_directories(tst_passwordstore PRIVATE
    ../src
)

target_link_libraries(tst_passwordstore PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Test
    KF6::Wallet
    Qt6::Concurrent
)

add_test(NAME tst_passwordstore COMMAND tst_passwordstore)

qt_add_executable(tst_passwordfill
    passwords/tst_passwordfill.cpp
)

qt_add_resources(tst_passwordfill "passwords_scripts_fill"
    PREFIX "/scripts"
    BASE "${CMAKE_SOURCE_DIR}/src/passwords/bridge"
    FILES
        ${CMAKE_SOURCE_DIR}/src/passwords/bridge/passwords.js
        ${CMAKE_SOURCE_DIR}/src/passwords/bridge/usernamefield.js
)

target_link_libraries(tst_passwordfill PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Gui
    Qt6::Test
    Qt6::WebEngineCore
)

add_test(NAME tst_passwordfill COMMAND tst_passwordfill)
set_tests_properties(tst_passwordfill PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
    TIMEOUT 120
)

qt_add_executable(tst_passwordimport
    passwords/tst_passwordimport.cpp
)

target_include_directories(tst_passwordimport PRIVATE
    ../src
)

target_compile_definitions(tst_passwordimport PRIVATE
    KONDOR_TEST_DATA_DIR="${CMAKE_CURRENT_SOURCE_DIR}/data"
)

target_link_libraries(tst_passwordimport PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Test
    KF6::Wallet
    Qt6::Concurrent
)

add_test(NAME tst_passwordimport COMMAND tst_passwordimport)

# No test may reach the session wallet: PasswordStore goes straight to "unavailable".
get_property(kondor_all_tests DIRECTORY PROPERTY TESTS)
set_property(TEST ${kondor_all_tests} APPEND PROPERTY ENVIRONMENT "KONDOR_NO_KWALLET=1")

qt_add_executable(tst_extensionloader
    extensions/install/tst_extensionloader.cpp
)

target_include_directories(tst_extensionloader PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_compile_definitions(tst_extensionloader PRIVATE
    KONDOR_TEST_DATA_DIR="${CMAKE_CURRENT_SOURCE_DIR}/data"
)

target_link_libraries(tst_extensionloader PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::WebEngineCore
    Qt6::WebEngineQuick
    Qt6::Test
    Qt6::Concurrent
)

add_test(NAME tst_extensionloader COMMAND tst_extensionloader)
set_tests_properties(tst_extensionloader PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

set(KONDOR_EXTENSION_BRIDGE_TEST_LIBRARIES
    Qt6::Concurrent
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Network
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Sql
    Qt6::Test
    Qt6::WebChannel
    Qt6::WebEngineQuick
    KF6::Wallet
    KF6::Archive
)

qt_add_executable(tst_extensions
    extensions/tst_extensions.cpp
    extensions/package/tst_extensionpackage.cpp
    extensions/scripts/tst_extensionscripts.cpp
    extensions/install/tst_extensioninstall.cpp
    extensions/install/tst_extensionreplace.cpp
    extensions/bridge/tst_extensionbridge.cpp
    extensions/bridge/tst_extensionbridgetabs.cpp
    extensions/catalog/tst_extensioncatalog.cpp
    extensions/catalog/tst_extensionupdates.cpp
    extensions/tst_extensionsui.cpp
    extensions/tst_extensiondialogs.cpp
    extensions/bridge/tst_extensionpages.cpp
    passwords/tst_passwordsui.cpp
)

qt_add_resources(tst_extensions "extension_scripts"
    PREFIX "/scripts"
    BASE "${CMAKE_SOURCE_DIR}/src/extensions/bridge"
    FILES
        ${CMAKE_SOURCE_DIR}/src/extensions/bridge/channel.js
        ${CMAKE_SOURCE_DIR}/src/extensions/bridge/extensionruntime.js
)

qt_add_resources(tst_extensions "passwords_script"
    PREFIX "/scripts"
    BASE "${CMAKE_SOURCE_DIR}/src/passwords/bridge"
    FILES
        ${CMAKE_SOURCE_DIR}/src/passwords/bridge/passwords.js
)

target_compile_definitions(tst_extensions PRIVATE
    KONDOR_TEST_DATA_DIR="${CMAKE_CURRENT_SOURCE_DIR}/data"
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_extensions PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_extensions PRIVATE
    kondor_testlib
    ${KONDOR_EXTENSION_BRIDGE_TEST_LIBRARIES}
)

add_test(NAME tst_extensions COMMAND tst_extensions)
set_tests_properties(tst_extensions PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1;KONDOR_NO_KWALLET=1"
    TIMEOUT 300
)

qt_add_executable(tst_extensioncall
    extensions/bridge/tst_extensioncall.cpp
)

qt_add_resources(tst_extensioncall "extension_scripts_call"
    PREFIX "/scripts"
    BASE "${CMAKE_SOURCE_DIR}/src/extensions/bridge"
    FILES
        ${CMAKE_SOURCE_DIR}/src/extensions/bridge/channel.js
        ${CMAKE_SOURCE_DIR}/src/extensions/bridge/extensionruntime.js
)

qt_add_resources(tst_extensioncall "passwords_script_call"
    PREFIX "/scripts"
    BASE "${CMAKE_SOURCE_DIR}/src/passwords/bridge"
    FILES
        ${CMAKE_SOURCE_DIR}/src/passwords/bridge/passwords.js
)

target_compile_definitions(tst_extensioncall PRIVATE
    KONDOR_TEST_DATA_DIR="${CMAKE_CURRENT_SOURCE_DIR}/data"
)

target_include_directories(tst_extensioncall PRIVATE
    ../src
)

target_link_libraries(tst_extensioncall PRIVATE
    kondor_testlib
    ${KONDOR_EXTENSION_BRIDGE_TEST_LIBRARIES}
)

add_test(NAME tst_extensioncall COMMAND tst_extensioncall)
set_tests_properties(tst_extensioncall PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1;KONDOR_NO_KWALLET=1"
    TIMEOUT 300
)

qt_add_executable(tst_extensionsettings
    extensions/state/tst_extensionsettings.cpp
)

target_include_directories(tst_extensionsettings PRIVATE
    ../src
)

target_link_libraries(tst_extensionsettings PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_extensionsettings COMMAND tst_extensionsettings)

qt_add_executable(tst_catalogentry
    extensions/catalog/tst_catalogentry.cpp
)

target_include_directories(tst_catalogentry PRIVATE
    ../src
)

target_link_libraries(tst_catalogentry PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Gui
    Qt6::Test
    KF6::Archive
)

add_test(NAME tst_catalogentry COMMAND tst_catalogentry)

qt_add_executable(tst_manifestvalidator
    extensions/manifest/tst_manifestvalidator.cpp
)

target_include_directories(tst_manifestvalidator PRIVATE
    ../src
)

target_link_libraries(tst_manifestvalidator PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Gui
    Qt6::Test
    KF6::Archive
)

add_test(NAME tst_manifestvalidator COMMAND tst_manifestvalidator)

qt_add_executable(tst_contentscriptbuilder
    extensions/scripts/tst_contentscriptbuilder.cpp
)

qt_add_resources(tst_contentscriptbuilder "extension_scripts_builder"
    PREFIX "/scripts"
    BASE "${CMAKE_SOURCE_DIR}/src/extensions/bridge"
    FILES
        ${CMAKE_SOURCE_DIR}/src/extensions/bridge/extensionruntime.js
)

target_compile_definitions(tst_contentscriptbuilder PRIVATE
    KONDOR_TEST_DATA_DIR="${CMAKE_CURRENT_SOURCE_DIR}/data"
)

target_include_directories(tst_contentscriptbuilder PRIVATE
    ../src
)

target_link_libraries(tst_contentscriptbuilder PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Gui
    Qt6::Test
    Qt6::WebEngineCore
    KF6::Archive
)

add_test(NAME tst_contentscriptbuilder COMMAND tst_contentscriptbuilder)

qt_add_executable(tst_extensionstorage
    extensions/state/tst_extensionstorage.cpp
)

target_include_directories(tst_extensionstorage PRIVATE
    ../src
)

target_link_libraries(tst_extensionstorage PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Sql
    Qt6::Test
)

add_test(NAME tst_extensionstorage COMMAND tst_extensionstorage)

qt_add_executable(tst_database
    core/tst_database.cpp
)

target_include_directories(tst_database PRIVATE
    ../src
)

target_link_libraries(tst_database PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Sql
    Qt6::Test
)

add_test(NAME tst_database COMMAND tst_database)

qt_add_executable(tst_historymanager
    history/tst_historymanager.cpp
)

target_include_directories(tst_historymanager PRIVATE
    ../src
)

target_link_libraries(tst_historymanager PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::Sql
    Qt6::Test
)

add_test(NAME tst_historymanager COMMAND tst_historymanager)

qt_add_executable(tst_transferspeed
    downloads/tst_transferspeed.cpp
)

target_include_directories(tst_transferspeed PRIVATE
    ../src
)

target_link_libraries(tst_transferspeed PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_transferspeed COMMAND tst_transferspeed)

qt_add_executable(tst_bookmarkhtmlparser
    bookmarks/import/tst_bookmarkhtmlparser.cpp
)

target_include_directories(tst_bookmarkhtmlparser PRIVATE
    ../src
)

target_link_libraries(tst_bookmarkhtmlparser PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Sql
    Qt6::Test
)

add_test(NAME tst_bookmarkhtmlparser COMMAND tst_bookmarkhtmlparser)
set_tests_properties(tst_bookmarkhtmlparser PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen"
)

qt_add_executable(tst_passwordimportplan
    passwords/tst_passwordimportplan.cpp
)

target_include_directories(tst_passwordimportplan PRIVATE
    ../src
)

target_link_libraries(tst_passwordimportplan PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_passwordimportplan COMMAND tst_passwordimportplan)

qt_add_executable(tst_passwordimportasync
    passwords/tst_passwordimportasync.cpp
)

target_include_directories(tst_passwordimportasync PRIVATE
    ../src
)

target_link_libraries(tst_passwordimportasync PRIVATE
    kondor_testlib
    Qt6::Concurrent
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_passwordimportasync COMMAND tst_passwordimportasync)

qt_add_executable(tst_passwordimportoutcome
    passwords/tst_passwordimportoutcome.cpp
)

target_include_directories(tst_passwordimportoutcome PRIVATE
    ../src
)

target_link_libraries(tst_passwordimportoutcome PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_passwordimportoutcome COMMAND tst_passwordimportoutcome)

qt_add_executable(tst_passwordimportfile
    passwords/tst_passwordimportfile.cpp
)

target_include_directories(tst_passwordimportfile PRIVATE
    ../src
)

target_link_libraries(tst_passwordimportfile PRIVATE
    kondor_testlib
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_passwordimportfile COMMAND tst_passwordimportfile)
