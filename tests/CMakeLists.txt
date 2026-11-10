qt_add_executable(tst_addressresolver
    tst_addressresolver.cpp
    ../src/addressresolver.cpp
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
    tst_startupurl.cpp
    ../src/startupurl.cpp
    ../src/addressresolver.cpp
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
    tst_tabmodel.cpp
    ../src/tabmodel.cpp
    ../src/tab.cpp
    ../src/profilemanager.cpp
    ../src/addressresolver.cpp
    ../src/settings.cpp
    ../src/downloadmanager.cpp
    ../src/notifier.cpp
    ../src/historymanager.cpp
    ../src/historymodel.cpp
    ../src/database.cpp
    ../src/faviconstore.cpp
)

target_include_directories(tst_tabmodel PRIVATE
    ../src
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
)

add_test(NAME tst_tabmodel COMMAND tst_tabmodel)
set_tests_properties(tst_tabmodel PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_addresssuggestions
    tst_addresssuggestions.cpp
    ../src/tab.cpp
    ../src/tabmodel.cpp
    ../src/profilemanager.cpp
    ../src/addressresolver.cpp
    ../src/settings.cpp
    ../src/downloadmanager.cpp
    ../src/notifier.cpp
    ../src/historymanager.cpp
    ../src/historymodel.cpp
    ../src/database.cpp
    ../src/faviconstore.cpp
    ../src/bookmarkmanager.cpp
    ../src/bookmarkmodel.cpp
)

target_compile_definitions(tst_addresssuggestions PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
)

target_include_directories(tst_addresssuggestions PRIVATE
    ../src
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
)

add_test(NAME tst_addresssuggestions COMMAND tst_addresssuggestions)
set_tests_properties(tst_addresssuggestions PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_bookmarks
    tst_bookmarks.cpp
    ../src/bookmarkmanager.cpp
    ../src/bookmarkmodel.cpp
    ../src/database.cpp
)

target_include_directories(tst_bookmarks PRIVATE
    ../src
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
    tst_bookmarkswindow.cpp
    ../src/bookmarkmanager.cpp
    ../src/bookmarkmodel.cpp
    ../src/database.cpp
    ../src/tab.cpp
    ../src/tabmodel.cpp
    ../src/profilemanager.cpp
    ../src/addressresolver.cpp
    ../src/settings.cpp
    ../src/downloadmanager.cpp
    ../src/notifier.cpp
    ../src/historymanager.cpp
    ../src/historymodel.cpp
    ../src/faviconstore.cpp
)

target_compile_definitions(tst_bookmarkswindow PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
)

target_include_directories(tst_bookmarkswindow PRIVATE
    ../src
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
)

add_test(NAME tst_bookmarkswindow COMMAND tst_bookmarkswindow)
set_tests_properties(tst_bookmarkswindow PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_topsites
    tst_topsites.cpp
    ../src/historymanager.cpp
    ../src/historymodel.cpp
    ../src/database.cpp
    ../src/faviconstore.cpp
    ../src/settings.cpp
)

target_include_directories(tst_topsites PRIVATE
    ../src
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
    tst_faviconstore.cpp
    ../src/faviconstore.cpp
    ../src/historymanager.cpp
    ../src/historymodel.cpp
    ../src/database.cpp
    ../src/settings.cpp
)

target_include_directories(tst_faviconstore PRIVATE
    ../src
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
    tst_aboutinfo.cpp
    ../src/aboutinfo.cpp
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
    tst_settings.cpp
    ../src/settings.cpp
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
    tst_settingswindow.cpp
    ../src/tab.cpp
    ../src/tabmodel.cpp
    ../src/profilemanager.cpp
    ../src/addressresolver.cpp
    ../src/settings.cpp
    ../src/downloadmanager.cpp
    ../src/notifier.cpp
    ../src/historymanager.cpp
    ../src/historymodel.cpp
    ../src/database.cpp
    ../src/faviconstore.cpp
)

target_compile_definitions(tst_settingswindow PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
)

target_include_directories(tst_settingswindow PRIVATE
    ../src
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
)

add_test(NAME tst_settingswindow COMMAND tst_settingswindow)
set_tests_properties(tst_settingswindow PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)

qt_add_executable(tst_sitepermissions
    tst_sitepermissions.cpp
    ../src/tab.cpp
    ../src/profilemanager.cpp
    ../src/addressresolver.cpp
    ../src/settings.cpp
    ../src/downloadmanager.cpp
    ../src/notifier.cpp
    ../src/historymanager.cpp
    ../src/historymodel.cpp
    ../src/database.cpp
    ../src/faviconstore.cpp
)

target_compile_definitions(tst_sitepermissions PRIVATE
    KONDOR_QML_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../qml"
)

target_include_directories(tst_sitepermissions PRIVATE
    ../src
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
)

add_test(NAME tst_sitepermissions COMMAND tst_sitepermissions)
set_tests_properties(tst_sitepermissions PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1"
)
