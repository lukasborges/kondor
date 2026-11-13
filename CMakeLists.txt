cmake_minimum_required(VERSION 3.21)
project(Kondor VERSION 0.2.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 6.8 REQUIRED COMPONENTS
    Concurrent
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
    WebChannel
    Widgets
)
find_package(KF6Wallet REQUIRED)
find_package(KF6Archive REQUIRED)

include(GNUInstallDirs)
qt_standard_project_setup(REQUIRES 6.8)

qt_add_executable(kondor
    src/app/main.cpp
)

include(cmake/KondorSources.cmake)

option(BUILD_TESTING "Build tests" ON)

qt_add_qml_module(kondor
    URI Kondor
    VERSION 1.0
    QML_FILES
        qml/app/BrowserWindow.qml
        qml/app/WindowTabController.qml
        qml/app/FullScreenController.qml
        qml/app/WindowCloseGuard.qml
        qml/app/WindowDialogs.qml
        qml/app/PageFileDialogs.qml
        qml/app/BrowserActions.qml
        qml/app/BrowserShortcuts.qml
        qml/app/NavigationToolBar.qml
        qml/app/PageArea.qml
        qml/browser/AddressBar.qml
        qml/browser/AddressCompleter.qml
        qml/browser/AddressBarButtons.qml
        qml/site/SiteSecurityButton.qml
        qml/adblock/AdBlockButton.qml
        qml/browser/ZoomButton.qml
        qml/passwords/PasswordButton.qml
        qml/browser/ReaderButton.qml
        qml/bookmarks/BookmarkButton.qml
        qml/bookmarks/BookmarkEditorPopup.qml
        qml/downloads/DownloadSaveDialog.qml
        qml/common/LocalPath.qml
        qml/browser/TabStrip.qml
        qml/browser/TabStripScroller.qml
        qml/browser/TabWidthFreeze.qml
        qml/browser/TabStripTaps.qml
        qml/browser/TabStripWheel.qml
        qml/browser/TabStripScrollButton.qml
        qml/browser/TabDragHandler.qml
        qml/browser/TabSlideAnimation.qml
        qml/browser/WebViewTab.qml
        qml/browser/CertificateErrorHandler.qml
        qml/browser/PageOutput.qml
        qml/browser/PageScriptBridges.qml
        qml/browser/PageView.qml
        qml/browser/PageZoom.qml
        qml/browser/ReaderMode.qml
        qml/browser/ReaderStyle.qml
        qml/browser/TabCommands.qml
        qml/browser/PageContextMenu.qml
        qml/browser/PageMenuEntries.qml
        qml/browser/PageMenuActions.qml
        qml/browser/SpellCheckLanguagesMenu.qml
        qml/browser/ReaderControls.qml
        qml/browser/NewTabPage.qml
        qml/browser/TopSitesGrid.qml
        qml/browser/TopSiteMenu.qml
        qml/browser/TabButtonDelegate.qml
        qml/browser/TabContextMenu.qml
        qml/common/InlineBar.qml
        qml/common/ConfirmDialog.qml
        qml/browser/FindBar.qml
        qml/site/PermissionBar.qml
        qml/passwords/AddPasswordDialog.qml
        qml/passwords/ImportPasswordsDialog.qml
        qml/passwords/PasswordBar.qml
        qml/browser/FullScreenHint.qml
        qml/site/PermissionTypeInfo.qml
        qml/site/SitePermissionsDialog.qml
        qml/site/SiteInfoPopup.qml
        qml/site/SiteSecurityState.qml
        qml/adblock/AdBlockPopup.qml
        qml/browser/CertificateErrorPage.qml
        qml/browser/CrashedPage.qml
        qml/history/HistoryWindow.qml
        qml/history/HistoryList.qml
        qml/history/HistoryEntryMenu.qml
        qml/history/ClearHistoryDialog.qml
        qml/settings/SettingsWindow.qml
        qml/settings/SettingsDraft.qml
        qml/settings/SettingsPages.qml
        qml/settings/SettingsSidebar.qml
        qml/settings/SettingsPageHeader.qml
        qml/settings/SettingsButtonBar.qml
        qml/settings/SettingsPageStack.qml
        qml/settings/GeneralSettingsPage.qml
        qml/settings/SearchSettingsPage.qml
        qml/settings/DownloadsSettingsPage.qml
        qml/settings/PrivacySettingsPage.qml
        qml/settings/SpellingSettingsPage.qml
        qml/passwords/PasswordsPage.qml
        qml/passwords/RevealedPasswords.qml
        qml/passwords/NeverSavedTab.qml
        qml/passwords/SavedPasswordsTab.qml
        qml/passwords/SavedPasswordsList.qml
        qml/passwords/SavedPasswordDelegate.qml
        qml/passwords/RowToolButton.qml
        qml/passwords/PasswordsFrame.qml
        qml/passwords/ImportMessage.qml
        qml/passwords/ImportResult.qml
        qml/downloads/DownloadsPopup.qml
        qml/downloads/DownloadDelegate.qml
        qml/downloads/DownloadStatus.qml
        qml/bookmarks/BookmarksBar.qml
        qml/bookmarks/BookmarkMenu.qml
        qml/app/MainMenu.qml
        qml/app/HistoryMenu.qml
        qml/app/ZoomMenuRow.qml
        qml/bookmarks/BookmarksWindow.qml
        qml/bookmarks/BookmarkSelection.qml
        qml/bookmarks/BookmarkFolderTree.qml
        qml/bookmarks/BookmarkDragController.qml
        qml/bookmarks/BookmarkDropTargets.qml
        qml/bookmarks/BookmarkDragPreview.qml
        qml/bookmarks/BookmarksToolBar.qml
        qml/bookmarks/BookmarkFolderPane.qml
        qml/bookmarks/BookmarkItemPane.qml
        qml/bookmarks/BookmarkItemDelegate.qml
        qml/bookmarks/BookmarkItemContextMenu.qml
        qml/bookmarks/NewBookmarkFolderDialog.qml
        qml/bookmarks/RenameBookmarkDialog.qml
        qml/bookmarks/DeleteBookmarkDialog.qml
        qml/common/SiteIcon.qml
        qml/common/SiteMenuItem.qml
        qml/browser/AddressSuggestions.qml
        qml/app/AboutWindow.qml
        qml/app/AboutTab.qml
        qml/app/ComponentsTab.qml
        qml/app/AuthorsTab.qml
        qml/app/LicenseWindow.qml
        qml/extensions/ExtensionIcon.qml
        qml/extensions/ExtensionsPage.qml
        qml/extensions/ExtensionCatalogDialog.qml
        qml/extensions/InstallExtensionDialog.qml
        qml/extensions/ExtensionSettingsDialog.qml
        qml/extensions/ExtensionSettingControls.qml
        qml/extensions/ExtensionSitesSection.qml
        qml/extensions/ExtensionDelegate.qml
        qml/extensions/ExtensionsMenu.qml
    SOURCES
        src/app/aboutinfo.h
        src/app/aboutinfo.cpp
        src/browser/addressresolver.h
        src/browser/addressresolver.cpp
        ${KONDOR_TAB_SOURCES}
        ${KONDOR_TAB_MODEL_SOURCES}
        ${KONDOR_PROFILE_MANAGER_SOURCES}
        src/app/startupargs.h
        src/app/startupargs.cpp
        ${KONDOR_APP_SOURCES}
        ${KONDOR_SETTINGS_SOURCES}
        ${KONDOR_SESSION_SOURCES}
        ${KONDOR_DATABASE_SOURCES}
        ${KONDOR_HISTORY_MANAGER_SOURCES}
        ${KONDOR_HISTORY_MODEL_SOURCES}
        ${KONDOR_DOWNLOAD_MANAGER_SOURCES}
        src/core/filehelper.h
        src/core/filehelper.cpp
        ${KONDOR_NOTIFIER_SOURCES}
        ${KONDOR_BOOKMARK_MANAGER_SOURCES}
        src/bookmarks/bookmarkrow.h
        ${KONDOR_BOOKMARK_MODEL_SOURCES}
        src/browser/faviconstore.h
        src/browser/faviconstore.cpp
        src/extensions/extensionloader.h
        src/extensions/extensionloader.cpp
        ${KONDOR_SUGGESTION_SOURCES}
        src/browser/zoommanager.h
        src/browser/zoommanager.cpp
        ${KONDOR_ADBLOCK_SOURCES}
        ${KONDOR_PASSWORD_STORE_SOURCES}
        src/passwords/passwordbridge.h
        src/passwords/passwordbridge.cpp
        ${KONDOR_EXTENSION_PACKAGE_SOURCES}
        ${KONDOR_EXTENSION_MANAGER_SOURCES}
        ${KONDOR_EXTENSION_BRIDGE_SOURCES}
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

qt_add_resources(kondor "reader"
    PREFIX "/reader"
    BASE "${CMAKE_SOURCE_DIR}/3rdparty/readability"
    FILES
        3rdparty/readability/Readability.js
        3rdparty/readability/Readability-readerable.js
        3rdparty/readability/template.html
)

qt_add_resources(kondor "passwords_script"
    PREFIX "/scripts"
    BASE "${CMAKE_SOURCE_DIR}/src/passwords"
    FILES
        src/passwords/passwords.js
        src/passwords/usernamefield.js
)

qt_add_resources(kondor "extension_scripts"
    PREFIX "/scripts"
    BASE "${CMAKE_SOURCE_DIR}/src/extensions"
    FILES
        src/extensions/channel.js
        src/extensions/extensionruntime.js
)

qt_add_resources(kondor "license"
    PREFIX "/"
    FILES
        LICENSE
)

target_compile_definitions(kondor PRIVATE
    PROJECT_VERSION="${PROJECT_VERSION}"
)

file(GLOB KONDOR_SOURCE_FOLDERS LIST_DIRECTORIES true "${CMAKE_CURRENT_SOURCE_DIR}/src/*")
list(FILTER KONDOR_SOURCE_FOLDERS EXCLUDE REGEX "\\.(cpp|h|js)$")

# qmltyperegistrar includes the headers of the QML types by file name only
target_include_directories(kondor PRIVATE
    src
    ${KONDOR_SOURCE_FOLDERS}
)

target_link_libraries(kondor PRIVATE
    Qt6::Concurrent
    Qt6::Core
    Qt6::DBus
    Qt6::Gui
    Qt6::Network
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Sql
    Qt6::WebChannel
    Qt6::WebEngineCore
    Qt6::WebEngineQuick
    Qt6::Widgets
    KF6::Wallet
    KF6::Archive
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

# Spell checking dictionaries: Hunspell .dic/.aff files converted to the .bdic
# format Qt WebEngine reads. Chromium names them with a hyphen ("pt-BR").
set(KONDOR_SPELLCHECK_LANGS "en_US;pt_BR" CACHE STRING
    "Hunspell dictionaries (from /usr/share/hunspell) to convert and install")
find_program(QWEBENGINE_CONVERT_DICT qwebengine_convert_dict
    HINTS "${QT6_INSTALL_PREFIX}/${QT6_INSTALL_LIBEXECS}" /usr/lib64/qt6/libexec /usr/lib/qt6/libexec)
set(KONDOR_DICTIONARIES_DIR "${CMAKE_BINARY_DIR}/qtwebengine_dictionaries")
set(KONDOR_BDIC_FILES)
if(QWEBENGINE_CONVERT_DICT)
    foreach(lang IN LISTS KONDOR_SPELLCHECK_LANGS)
        set(dic "/usr/share/hunspell/${lang}.dic")
        string(REPLACE "_" "-" bdic_name "${lang}")
        if(EXISTS "${dic}")
            set(bdic "${KONDOR_DICTIONARIES_DIR}/${bdic_name}.bdic")
            add_custom_command(
                OUTPUT "${bdic}"
                COMMAND ${CMAKE_COMMAND} -E make_directory "${KONDOR_DICTIONARIES_DIR}"
                COMMAND ${CMAKE_COMMAND} -E env QT_QPA_PLATFORM=offscreen
                        "${QWEBENGINE_CONVERT_DICT}" "${dic}" "${bdic}"
                DEPENDS "${dic}"
                COMMENT "Converting the ${lang} dictionary"
                VERBATIM)
            list(APPEND KONDOR_BDIC_FILES "${bdic}")
        else()
            message(WARNING "Hunspell dictionary ${dic} not found: no ${lang} spell checking")
        endif()
    endforeach()
else()
    message(WARNING "qwebengine_convert_dict not found: spell checking dictionaries are not built")
endif()
if(KONDOR_BDIC_FILES)
    add_custom_target(kondor_dictionaries ALL DEPENDS ${KONDOR_BDIC_FILES})
    add_dependencies(kondor kondor_dictionaries)
    install(DIRECTORY "${KONDOR_DICTIONARIES_DIR}"
        DESTINATION ${CMAKE_INSTALL_DATADIR}/kondor)
endif()

# Icon and menu entry (.desktop)
install(FILES packaging/kondor.desktop DESTINATION share/applications)
install(FILES packaging/io.github.lukasborges.Kondor.metainfo.xml DESTINATION share/metainfo)
install(FILES packaging/kondor-extension.xml DESTINATION share/mime/packages)
install(FILES packaging/kondor.png DESTINATION share/icons/hicolor/256x256/apps)
install(FILES packaging/kondor.svg DESTINATION share/icons/hicolor/scalable/apps)
