cmake_minimum_required(VERSION 3.21)
project(Kondor VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 6.5 REQUIRED COMPONENTS
    Core
    Gui
    Qml
    Quick
    QuickControls2
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
    SOURCES
        src/tab.h
        src/tab.cpp
        src/tabmodel.h
        src/tabmodel.cpp
        src/profilemanager.h
        src/profilemanager.cpp
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
    Qt6::WebEngineQuick
)

install(TARGETS kondor
    BUNDLE DESTINATION .
    RUNTIME DESTINATION bin
)
