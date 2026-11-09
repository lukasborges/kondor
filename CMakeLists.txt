cmake_minimum_required(VERSION 3.21)
project(Kondor VERSION 0.1.5 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 6.5 REQUIRED COMPONENTS
    Core
    Gui
    Qml
    Quick
    QuickControls2
    Sql
    WebEngineQuick
)

qt_standard_project_setup(REQUIRES 6.5)

qt_add_executable(kondor
    src/main.cpp
)

qt_add_qml_module(kondor
    URI Kondor
    VERSION 1.0
    QML_FILES
        qml/Main.qml
        qml/WebViewTab.qml
        qml/HistoryWindow.qml
        qml/SettingsWindow.qml
    SOURCES
        src/tab.h
        src/tab.cpp
        src/tabmodel.h
        src/tabmodel.cpp
        src/profilemanager.h
        src/profilemanager.cpp
        src/settings.h
        src/settings.cpp
        src/database.h
        src/database.cpp
        src/historymanager.h
        src/historymanager.cpp
        src/historymodel.h
        src/historymodel.cpp
)

qt_add_resources(kondor "app_icon"
    PREFIX "/"
    FILES
        packaging/kondor.png
        packaging/kondor.svg
)

target_include_directories(kondor PRIVATE
    src
)

target_link_libraries(kondor PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Sql
    Qt6::WebEngineQuick
)

install(TARGETS kondor
    BUNDLE DESTINATION .
    RUNTIME DESTINATION bin
)

# Ícone e entrada de menu (.desktop)
install(FILES packaging/kondor.desktop DESTINATION share/applications)
install(FILES packaging/kondor.png DESTINATION share/icons/hicolor/256x256/apps)
install(FILES packaging/kondor.svg DESTINATION share/icons/hicolor/scalable/apps)
