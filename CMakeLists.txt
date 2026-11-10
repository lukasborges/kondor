cmake_minimum_required(VERSION 3.21)
project(Kondor VERSION 0.1.5 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 6.8 REQUIRED COMPONENTS
    Core
    DBus
    Gui
    LinguistTools
    Network
    Qml
    Quick
    QuickControls2
    Sql
    WebEngineCore
    WebEngineQuick
    Widgets
)

qt_standard_project_setup(REQUIRES 6.8)

qt_add_executable(kondor
    src/main.cpp
)

option(BUILD_TESTING "Build tests" ON)

qt_add_qml_module(kondor
    URI Kondor
    VERSION 1.0
    QML_FILES
        qml/Main.qml
        qml/WebViewTab.qml
        qml/PageContextMenu.qml
        qml/NewTabPage.qml
        qml/TabButtonDelegate.qml
        qml/TabContextMenu.qml
        qml/InlineBar.qml
        qml/FindBar.qml
        qml/PermissionBar.qml
        qml/FullScreenHint.qml
        qml/PermissionTypeInfo.qml
        qml/SitePermissionsDialog.qml
        qml/SiteInfoPopup.qml
        qml/CertificateErrorPage.qml
        qml/CrashedPage.qml
        qml/HistoryWindow.qml
        qml/SettingsWindow.qml
        qml/DownloadsPopup.qml
        qml/BookmarksBar.qml
        qml/BookmarkMenu.qml
        qml/BookmarksWindow.qml
        qml/SiteIcon.qml
        qml/AddressSuggestions.qml
        qml/AboutWindow.qml
    SOURCES
        src/aboutinfo.h
        src/aboutinfo.cpp
        src/addressresolver.h
        src/addressresolver.cpp
        src/tab.h
        src/tab.cpp
        src/tabmodel.h
        src/tabmodel.cpp
        src/profilemanager.h
        src/profilemanager.cpp
        src/startupargs.h
        src/startupargs.cpp
        src/startupurl.h
        src/startupurl.cpp
        src/settings.h
        src/settings.cpp
        src/sessionmanager.h
        src/sessionmanager.cpp
        src/database.h
        src/database.cpp
        src/historymanager.h
        src/historymanager.cpp
        src/historymodel.h
        src/historymodel.cpp
        src/downloadmanager.h
        src/downloadmanager.cpp
        src/notifier.h
        src/notifier.cpp
        src/bookmarkmanager.h
        src/bookmarkmanager.cpp
        src/bookmarkmodel.h
        src/bookmarkmodel.cpp
        src/faviconstore.h
        src/faviconstore.cpp
        src/searchsuggestions.h
        src/searchsuggestions.cpp
)

qt_add_translations(kondor
    TS_FILES
        i18n/kondor_ca.ts
        i18n/kondor_cs.ts
        i18n/kondor_de.ts
        i18n/kondor_es.ts
        i18n/kondor_fr.ts
        i18n/kondor_it.ts
        i18n/kondor_ja.ts
        i18n/kondor_ko.ts
        i18n/kondor_nl.ts
        i18n/kondor_pl.ts
        i18n/kondor_pt_BR.ts
        i18n/kondor_pt_PT.ts
        i18n/kondor_ru.ts
        i18n/kondor_sv.ts
        i18n/kondor_tr.ts
        i18n/kondor_uk.ts
        i18n/kondor_zh_CN.ts
        i18n/kondor_zh_TW.ts
    RESOURCE_PREFIX /i18n
    LUPDATE_OPTIONS -no-obsolete)

qt_add_resources(kondor "app_icon"
    PREFIX "/"
    FILES
        packaging/kondor.png
        packaging/kondor.svg
)

qt_add_resources(kondor "license"
    PREFIX "/"
    FILES
        LICENSE
)

target_compile_definitions(kondor PRIVATE
    PROJECT_VERSION="${PROJECT_VERSION}"
)

target_include_directories(kondor PRIVATE
    src
)

target_link_libraries(kondor PRIVATE
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Network
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Sql
    Qt6::WebEngineCore
    Qt6::WebEngineQuick
    Qt6::Widgets
)

if(BUILD_TESTING)
    enable_testing()
    find_package(Qt6 REQUIRED COMPONENTS Test)
    add_subdirectory(tests)
endif()

install(TARGETS kondor
    BUNDLE DESTINATION .
    RUNTIME DESTINATION bin
)

# Icon and menu entry (.desktop)
install(FILES packaging/kondor.desktop DESTINATION share/applications)
install(FILES packaging/kondor.png DESTINATION share/icons/hicolor/256x256/apps)
install(FILES packaging/kondor.svg DESTINATION share/icons/hicolor/scalable/apps)
