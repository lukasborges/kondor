set(KONDOR_TEST_QML_IMPORT_DIR "${CMAKE_CURRENT_BINARY_DIR}/qmlimport")
file(GLOB KONDOR_QML_SOURCES "${CMAKE_SOURCE_DIR}/qml/*/*.qml")
set(KONDOR_QMLDIR_CONTENT "module Kondor\n")
foreach(qml_file IN LISTS KONDOR_QML_SOURCES)
    get_filename_component(qml_type "${qml_file}" NAME_WE)
    file(RELATIVE_PATH qml_relative "${KONDOR_TEST_QML_IMPORT_DIR}/Kondor" "${qml_file}")
    string(APPEND KONDOR_QMLDIR_CONTENT "${qml_type} 1.0 ${qml_relative}\n")
endforeach()
file(WRITE "${KONDOR_TEST_QML_IMPORT_DIR}/Kondor/qmldir" "${KONDOR_QMLDIR_CONTENT}")

qt_add_executable(tst_addressresolver
    browser/tst_addressresolver.cpp
    ../src/browser/addressresolver.cpp
)

target_include_directories(tst_addressresolver PRIVATE
    ../src
)

target_link_libraries(tst_addressresolver PRIVATE
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_addressresolver COMMAND tst_addressresolver)

qt_add_executable(tst_startupurl
    app/tst_startupurl.cpp
    ../src/app/startupurl.cpp
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
)

target_include_directories(tst_startupurl PRIVATE
    ../src
)

target_link_libraries(tst_startupurl PRIVATE
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_startupurl COMMAND tst_startupurl)

qt_add_executable(tst_tabmodel
    browser/tst_tabmodel.cpp
    browser/tst_recentlyclosedtabs.cpp
    browser/tst_tabnewtabpage.cpp
    browser/tst_tabpinning.cpp
    ${KONDOR_TAB_MODEL_SOURCES}
    ${KONDOR_TAB_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_ADBLOCK_SOURCES}
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ../src/browser/faviconstore.cpp
)

target_include_directories(tst_tabmodel PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_tabmodel PRIVATE
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
)

add_test(NAME tst_tabmodel COMMAND tst_tabmodel)
set_tests_properties(tst_tabmodel PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_tabpasswords
    browser/tst_tabpasswords.cpp
    ${KONDOR_TAB_MODEL_SOURCES}
    ${KONDOR_TAB_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_ADBLOCK_SOURCES}
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ../src/browser/faviconstore.cpp
)

target_include_directories(tst_tabpasswords PRIVATE
    ../src
)

target_link_libraries(tst_tabpasswords PRIVATE
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
)

add_test(NAME tst_tabpasswords COMMAND tst_tabpasswords)
set_tests_properties(tst_tabpasswords PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_tabsecurity
    browser/tst_tabsecurity.cpp
    ${KONDOR_TAB_MODEL_SOURCES}
    ${KONDOR_TAB_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_ADBLOCK_SOURCES}
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ../src/browser/faviconstore.cpp
)

target_include_directories(tst_tabsecurity PRIVATE
    ../src
)

target_link_libraries(tst_tabsecurity PRIVATE
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
)

add_test(NAME tst_tabsecurity COMMAND tst_tabsecurity)
set_tests_properties(tst_tabsecurity PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_addresssuggestions
    browser/tst_addresssuggestions.cpp
    ${KONDOR_TAB_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_TAB_MODEL_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_ADBLOCK_SOURCES}
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ../src/browser/faviconstore.cpp
    ${KONDOR_BOOKMARK_MANAGER_SOURCES}
    ${KONDOR_BOOKMARK_MODEL_SOURCES}
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
)

add_test(NAME tst_addresssuggestions COMMAND tst_addresssuggestions)
set_tests_properties(tst_addresssuggestions PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_addressbar
    browser/tst_addressbar.cpp
    ${KONDOR_TAB_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_TAB_MODEL_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_ADBLOCK_SOURCES}
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ../src/browser/faviconstore.cpp
    ${KONDOR_BOOKMARK_MANAGER_SOURCES}
    ${KONDOR_BOOKMARK_MODEL_SOURCES}
    ${KONDOR_SUGGESTION_SOURCES}
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
)

add_test(NAME tst_addressbar COMMAND tst_addressbar)
set_tests_properties(tst_addressbar PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_bookmarks
    bookmarks/tst_bookmarks.cpp
    bookmarks/tst_defaultbookmarks.cpp
    bookmarks/tst_bookmarktree.cpp
    bookmarks/tst_bookmarkimport.cpp
    ${KONDOR_BOOKMARK_MANAGER_SOURCES}
    ${KONDOR_BOOKMARK_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
)

target_include_directories(tst_bookmarks PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_bookmarks PRIVATE
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
    ${KONDOR_BOOKMARK_MANAGER_SOURCES}
    ${KONDOR_BOOKMARK_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ${KONDOR_TAB_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_TAB_MODEL_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_ADBLOCK_SOURCES}
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ../src/browser/faviconstore.cpp
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
)

add_test(NAME tst_bookmarkswindow COMMAND tst_bookmarkswindow)
set_tests_properties(tst_bookmarkswindow PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_mainmenu
    app/tst_mainmenu.cpp
    ${KONDOR_BOOKMARK_MANAGER_SOURCES}
    ${KONDOR_BOOKMARK_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ${KONDOR_TAB_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_TAB_MODEL_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_ADBLOCK_SOURCES}
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ../src/browser/faviconstore.cpp
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
)

add_test(NAME tst_mainmenu COMMAND tst_mainmenu)
set_tests_properties(tst_mainmenu PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_topsites
    history/tst_topsites.cpp
    history/tst_historysuggestions.cpp
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ../src/browser/faviconstore.cpp
    ${KONDOR_SETTINGS_SOURCES}
)

target_include_directories(tst_topsites PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_topsites PRIVATE
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
    ../src/browser/faviconstore.cpp
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ${KONDOR_SETTINGS_SOURCES}
)

target_include_directories(tst_faviconstore PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_faviconstore PRIVATE
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
    ../src/app/aboutinfo.cpp
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

qt_add_executable(tst_settings
    core/tst_settings.cpp
    ${KONDOR_SETTINGS_SOURCES}
)

target_include_directories(tst_settings PRIVATE
    ../src
)

target_link_libraries(tst_settings PRIVATE
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_settings COMMAND tst_settings)

qt_add_executable(tst_settingswindow
    settings/tst_settingswindow.cpp
    settings/tst_settingsapply.cpp
    settings/tst_settingsnavigation.cpp
    ${KONDOR_TAB_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_TAB_MODEL_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_ADBLOCK_SOURCES}
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ../src/browser/faviconstore.cpp
    ${KONDOR_EXTENSION_PACKAGE_SOURCES}
    ${KONDOR_EXTENSION_MANAGER_SOURCES}
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
)

add_test(NAME tst_settingswindow COMMAND tst_settingswindow)
set_tests_properties(tst_settingswindow PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_tabstrip
    browser/tst_tabstrip.cpp
    browser/tst_tabstripwidths.cpp
    browser/tst_tabstripclosing.cpp
    browser/tst_tabdrag.cpp
    browser/tst_tabdragscroll.cpp
    browser/tst_tabdragrelease.cpp
    ${KONDOR_TAB_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_TAB_MODEL_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_ADBLOCK_SOURCES}
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ../src/browser/faviconstore.cpp
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
)

add_test(NAME tst_tabstrip COMMAND tst_tabstrip)
set_tests_properties(tst_tabstrip PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_tabstripscroll
    browser/tst_tabstripscroll.cpp
    ${KONDOR_TAB_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_TAB_MODEL_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_ADBLOCK_SOURCES}
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ../src/browser/faviconstore.cpp
)

target_compile_definitions(tst_tabstripscroll PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_tabstripscroll PRIVATE
    ../src
)

target_link_libraries(tst_tabstripscroll PRIVATE
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
)

add_test(NAME tst_tabstripscroll COMMAND tst_tabstripscroll)
set_tests_properties(tst_tabstripscroll PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_sitepermissions
    site/tst_sitepermissions.cpp
    site/tst_sitepermissionsui.cpp
    ${KONDOR_TAB_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_ADBLOCK_SOURCES}
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ../src/browser/faviconstore.cpp
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
)

add_test(NAME tst_sitepermissions COMMAND tst_sitepermissions)
set_tests_properties(tst_sitepermissions PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_pagecontextmenu
    browser/tst_pagecontextmenu.cpp
    ${KONDOR_TAB_MODEL_SOURCES}
    ${KONDOR_TAB_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_ADBLOCK_SOURCES}
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ../src/browser/faviconstore.cpp
)

target_compile_definitions(tst_pagecontextmenu PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_pagecontextmenu PRIVATE
    ../src
)

target_link_libraries(tst_pagecontextmenu PRIVATE
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
    ${KONDOR_TAB_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_ADBLOCK_SOURCES}
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ../src/browser/faviconstore.cpp
)

target_compile_definitions(tst_permissiontypeinfo PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_permissiontypeinfo PRIVATE
    ../src
)

target_link_libraries(tst_permissiontypeinfo PRIVATE
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
    ${KONDOR_TAB_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_ADBLOCK_SOURCES}
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ../src/browser/faviconstore.cpp
)

target_compile_definitions(tst_downloadstatus PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
    KONDOR_QML_IMPORT_DIR="${KONDOR_TEST_QML_IMPORT_DIR}"
)

target_include_directories(tst_downloadstatus PRIVATE
    ../src
)

target_link_libraries(tst_downloadstatus PRIVATE
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
    ${KONDOR_SESSION_SOURCES}
    ${KONDOR_TAB_MODEL_SOURCES}
    ${KONDOR_TAB_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_ADBLOCK_SOURCES}
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ../src/browser/faviconstore.cpp
)

target_include_directories(tst_sessionmanager PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(tst_sessionmanager PRIVATE
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::Sql
    Qt6::Test
    Qt6::WebEngineQuick
    KF6::Wallet
)

add_test(NAME tst_sessionmanager COMMAND tst_sessionmanager)
set_tests_properties(tst_sessionmanager PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_singleinstance
    app/tst_singleinstance.cpp
    ../src/app/singleinstance.cpp
    ../src/app/singleinstancemessage.cpp
)

target_include_directories(tst_singleinstance PRIVATE
    ../src
)

target_link_libraries(tst_singleinstance PRIVATE
    Qt6::Core
    Qt6::Network
    Qt6::Test
)

add_test(NAME tst_singleinstance COMMAND tst_singleinstance)

qt_add_executable(tst_extensionpackages
    app/tst_extensionpackages.cpp
    ../src/app/extensionpackages.cpp
    ../src/extensions/packagesuffix.cpp
)

target_include_directories(tst_extensionpackages PRIVATE
    ../src
)

target_link_libraries(tst_extensionpackages PRIVATE
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_extensionpackages COMMAND tst_extensionpackages)

qt_add_executable(tst_filehelper
    core/tst_filehelper.cpp
    ../src/core/filehelper.cpp
)

target_include_directories(tst_filehelper PRIVATE
    ../src
)

target_link_libraries(tst_filehelper PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Test
)

add_test(NAME tst_filehelper COMMAND tst_filehelper)

qt_add_executable(tst_suggestionlist
    browser/tst_suggestionlist.cpp
    ../src/browser/suggestionlist.cpp
)

target_include_directories(tst_suggestionlist PRIVATE
    ../src
)

target_link_libraries(tst_suggestionlist PRIVATE
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_suggestionlist COMMAND tst_suggestionlist)

qt_add_executable(tst_zoommanager
    browser/tst_zoommanager.cpp
    ../src/browser/zoommanager.cpp
)

target_include_directories(tst_zoommanager PRIVATE
    ../src
)

target_link_libraries(tst_zoommanager PRIVATE
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
target_link_libraries(tst_settingswindow PRIVATE Qt6::Concurrent Qt6::Network)
target_link_libraries(tst_tabstrip PRIVATE Qt6::Concurrent Qt6::Network)
target_link_libraries(tst_tabstripscroll PRIVATE Qt6::Concurrent Qt6::Network)
target_link_libraries(tst_sitepermissions PRIVATE Qt6::Concurrent Qt6::Network)
target_link_libraries(tst_sessionmanager PRIVATE Qt6::Concurrent Qt6::Network)

qt_add_executable(tst_filterengine
    adblock/tst_filterengine.cpp
    ${KONDOR_FILTER_ENGINE_SOURCES}
)

target_include_directories(tst_filterengine PRIVATE
    ../src
)

target_link_libraries(tst_filterengine PRIVATE
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_filterengine COMMAND tst_filterengine)

qt_add_executable(tst_adblockallowlist
    adblock/tst_adblockallowlist.cpp
    ${KONDOR_ADBLOCK_SOURCES}
    ${KONDOR_SETTINGS_SOURCES}
)

target_include_directories(tst_adblockallowlist PRIVATE
    ../src
)

target_link_libraries(tst_adblockallowlist PRIVATE
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

qt_add_executable(tst_passwordstore
    passwords/tst_passwordstore.cpp
    ${KONDOR_PASSWORD_STORE_SOURCES}
)

target_include_directories(tst_passwordstore PRIVATE
    ../src
)

target_link_libraries(tst_passwordstore PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Test
    KF6::Wallet
)

add_test(NAME tst_passwordstore COMMAND tst_passwordstore)

qt_add_executable(tst_passwordimport
    passwords/tst_passwordimport.cpp
    ${KONDOR_PASSWORD_STORE_SOURCES}
)

target_include_directories(tst_passwordimport PRIVATE
    ../src
)

target_compile_definitions(tst_passwordimport PRIVATE
    KONDOR_TEST_DATA_DIR="${CMAKE_CURRENT_SOURCE_DIR}/data"
)

target_link_libraries(tst_passwordimport PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Test
    KF6::Wallet
)

add_test(NAME tst_passwordimport COMMAND tst_passwordimport)

# No test may reach the session wallet: PasswordStore goes straight to "unavailable".
get_property(kondor_all_tests DIRECTORY PROPERTY TESTS)
set_property(TEST ${kondor_all_tests} APPEND PROPERTY ENVIRONMENT "KONDOR_NO_KWALLET=1")

qt_add_executable(tst_extensionloader
    extensions/tst_extensionloader.cpp
    ../src/extensions/extensionloader.cpp
)

target_include_directories(tst_extensionloader PRIVATE
    ../src
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_compile_definitions(tst_extensionloader PRIVATE
    KONDOR_TEST_DATA_DIR="${CMAKE_CURRENT_SOURCE_DIR}/data"
)

target_link_libraries(tst_extensionloader PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::WebEngineCore
    Qt6::WebEngineQuick
    Qt6::Test
)

add_test(NAME tst_extensionloader COMMAND tst_extensionloader)
set_tests_properties(tst_extensionloader PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

set(KONDOR_EXTENSION_BRIDGE_TEST_SOURCES
    ${KONDOR_EXTENSION_BRIDGE_SOURCES}
    ${KONDOR_TAB_SOURCES}
    ${KONDOR_PASSWORD_STORE_SOURCES}
    ${KONDOR_PROFILE_MANAGER_SOURCES}
    ${KONDOR_ADBLOCK_SOURCES}
    ../src/browser/addressresolver.cpp
    ${KONDOR_SETTINGS_SOURCES}
    ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
    ${KONDOR_NOTIFIER_SOURCES}
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ../src/browser/faviconstore.cpp
    ${KONDOR_EXTENSION_PACKAGE_SOURCES}
    ${KONDOR_EXTENSION_MANAGER_SOURCES}
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
    extensions/tst_extensionpackage.cpp
    extensions/tst_extensionscripts.cpp
    extensions/tst_extensioninstall.cpp
    extensions/tst_extensionreplace.cpp
    extensions/tst_extensionbridge.cpp
    extensions/tst_extensionbridgetabs.cpp
    extensions/tst_extensioncatalog.cpp
    extensions/tst_extensionupdates.cpp
    extensions/tst_extensionsui.cpp
    extensions/tst_extensiondialogs.cpp
    extensions/tst_extensionpages.cpp
    ${KONDOR_EXTENSION_BRIDGE_TEST_SOURCES}
)

qt_add_resources(tst_extensions "extension_scripts"
    PREFIX "/scripts"
    BASE "${CMAKE_SOURCE_DIR}/src/extensions"
    FILES
        ${CMAKE_SOURCE_DIR}/src/extensions/channel.js
        ${CMAKE_SOURCE_DIR}/src/extensions/extensionruntime.js
)

qt_add_resources(tst_extensions "passwords_script"
    PREFIX "/scripts"
    BASE "${CMAKE_SOURCE_DIR}/src/passwords"
    FILES
        ${CMAKE_SOURCE_DIR}/src/passwords/passwords.js
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
    ${KONDOR_EXTENSION_BRIDGE_TEST_LIBRARIES}
)

add_test(NAME tst_extensions COMMAND tst_extensions)
set_tests_properties(tst_extensions PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1;KONDOR_NO_KWALLET=1"
    TIMEOUT 300
)

qt_add_executable(tst_extensioncall
    extensions/tst_extensioncall.cpp
    ${KONDOR_EXTENSION_BRIDGE_TEST_SOURCES}
)

qt_add_resources(tst_extensioncall "extension_scripts_call"
    PREFIX "/scripts"
    BASE "${CMAKE_SOURCE_DIR}/src/extensions"
    FILES
        ${CMAKE_SOURCE_DIR}/src/extensions/channel.js
        ${CMAKE_SOURCE_DIR}/src/extensions/extensionruntime.js
)

qt_add_resources(tst_extensioncall "passwords_script_call"
    PREFIX "/scripts"
    BASE "${CMAKE_SOURCE_DIR}/src/passwords"
    FILES
        ${CMAKE_SOURCE_DIR}/src/passwords/passwords.js
)

target_compile_definitions(tst_extensioncall PRIVATE
    KONDOR_TEST_DATA_DIR="${CMAKE_CURRENT_SOURCE_DIR}/data"
)

target_include_directories(tst_extensioncall PRIVATE
    ../src
)

target_link_libraries(tst_extensioncall PRIVATE
    ${KONDOR_EXTENSION_BRIDGE_TEST_LIBRARIES}
)

add_test(NAME tst_extensioncall COMMAND tst_extensioncall)
set_tests_properties(tst_extensioncall PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1;KONDOR_NO_KWALLET=1"
    TIMEOUT 300
)

qt_add_executable(tst_extensionsettings
    extensions/tst_extensionsettings.cpp
    ../src/extensions/extensionsettings.cpp
)

target_include_directories(tst_extensionsettings PRIVATE
    ../src
)

target_link_libraries(tst_extensionsettings PRIVATE
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_extensionsettings COMMAND tst_extensionsettings)

qt_add_executable(tst_catalogentry
    extensions/tst_catalogentry.cpp
    ../src/extensions/catalogentry.cpp
    ${KONDOR_EXTENSION_PACKAGE_SOURCES}
)

target_include_directories(tst_catalogentry PRIVATE
    ../src
)

target_link_libraries(tst_catalogentry PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Test
    KF6::Archive
)

add_test(NAME tst_catalogentry COMMAND tst_catalogentry)

qt_add_executable(tst_manifestvalidator
    extensions/tst_manifestvalidator.cpp
    ${KONDOR_EXTENSION_PACKAGE_SOURCES}
)

target_include_directories(tst_manifestvalidator PRIVATE
    ../src
)

target_link_libraries(tst_manifestvalidator PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Test
    KF6::Archive
)

add_test(NAME tst_manifestvalidator COMMAND tst_manifestvalidator)

qt_add_executable(tst_contentscriptbuilder
    extensions/tst_contentscriptbuilder.cpp
    ../src/extensions/contentscriptbuilder.cpp
    ${KONDOR_EXTENSION_PACKAGE_SOURCES}
)

qt_add_resources(tst_contentscriptbuilder "extension_scripts_builder"
    PREFIX "/scripts"
    BASE "${CMAKE_SOURCE_DIR}/src/extensions"
    FILES
        ${CMAKE_SOURCE_DIR}/src/extensions/extensionruntime.js
)

target_compile_definitions(tst_contentscriptbuilder PRIVATE
    KONDOR_TEST_DATA_DIR="${CMAKE_CURRENT_SOURCE_DIR}/data"
)

target_include_directories(tst_contentscriptbuilder PRIVATE
    ../src
)

target_link_libraries(tst_contentscriptbuilder PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Test
    Qt6::WebEngineCore
    KF6::Archive
)

add_test(NAME tst_contentscriptbuilder COMMAND tst_contentscriptbuilder)

qt_add_executable(tst_extensionstorage
    extensions/tst_extensionstorage.cpp
    ../src/extensions/extensionstorage.cpp
    ${KONDOR_DATABASE_SOURCES}
)

target_include_directories(tst_extensionstorage PRIVATE
    ../src
)

target_link_libraries(tst_extensionstorage PRIVATE
    Qt6::Core
    Qt6::Sql
    Qt6::Test
)

add_test(NAME tst_extensionstorage COMMAND tst_extensionstorage)

qt_add_executable(tst_database
    core/tst_database.cpp
    ${KONDOR_DATABASE_SOURCES}
)

target_include_directories(tst_database PRIVATE
    ../src
)

target_link_libraries(tst_database PRIVATE
    Qt6::Core
    Qt6::Sql
    Qt6::Test
)

add_test(NAME tst_database COMMAND tst_database)

qt_add_executable(tst_historymanager
    history/tst_historymanager.cpp
    ${KONDOR_HISTORY_MANAGER_SOURCES}
    ${KONDOR_HISTORY_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
    ../src/browser/faviconstore.cpp
    ${KONDOR_SETTINGS_SOURCES}
)

target_include_directories(tst_historymanager PRIVATE
    ../src
)

target_link_libraries(tst_historymanager PRIVATE
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
    ../src/downloads/transferspeed.cpp
)

target_include_directories(tst_transferspeed PRIVATE
    ../src
)

target_link_libraries(tst_transferspeed PRIVATE
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_transferspeed COMMAND tst_transferspeed)

qt_add_executable(tst_bookmarkhtmlparser
    bookmarks/tst_bookmarkhtmlparser.cpp
    ${KONDOR_BOOKMARK_MANAGER_SOURCES}
    ${KONDOR_BOOKMARK_MODEL_SOURCES}
    ${KONDOR_DATABASE_SOURCES}
)

target_include_directories(tst_bookmarkhtmlparser PRIVATE
    ../src
)

target_link_libraries(tst_bookmarkhtmlparser PRIVATE
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
    ../src/passwords/passwordimportplan.cpp
)

target_include_directories(tst_passwordimportplan PRIVATE
    ../src
)

target_link_libraries(tst_passwordimportplan PRIVATE
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_passwordimportplan COMMAND tst_passwordimportplan)

qt_add_executable(tst_passwordimportfile
    passwords/tst_passwordimportfile.cpp
    ../src/passwords/passwordimportfile.cpp
)

target_include_directories(tst_passwordimportfile PRIVATE
    ../src
)

target_link_libraries(tst_passwordimportfile PRIVATE
    Qt6::Core
    Qt6::Test
)

add_test(NAME tst_passwordimportfile COMMAND tst_passwordimportfile)
