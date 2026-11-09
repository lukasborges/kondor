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
