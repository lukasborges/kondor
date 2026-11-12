pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ApplicationWindow {
    id: root
    width: 860
    height: 600
    minimumWidth: 640
    minimumHeight: 480
    //: %1 is the application name
    title: qsTr("Configure — %1").arg(Qt.application.displayName)
    visible: false

    required property TabModel tabModel

    property int currentPage: 0
    property int generalTab: 0
    property int passwordsTab: 0
    property bool modified: false
    property bool defaultsEnabled: false

    onClosing: function(close) {
        close.accepted = false
        root.discardChanges()
    }

    onCurrentPageChanged: root.refresh()

    function refresh() {
        root.modified = optionsDraft.isModified()
        root.defaultsEnabled = !optionsDraft.isAtDefaults(pageCatalog.pages[root.currentPage].options)
    }

    function restoreDefaults() {
        optionsDraft.restoreDefaults(pageCatalog.pages[root.currentPage].options)
        root.refresh()
    }

    function applyChanges() {
        optionsDraft.apply()
        root.refresh()
    }

    function acceptAndClose() {
        root.applyChanges()
        root.discardChanges()
    }

    function discardChanges() {
        root.visible = false
    }

    function showWindow() {
        Settings.refreshDownloadDirectory()
        sidebar.clearSearch()
        optionsDraft.read()
        root.refresh()
        root.visible = true
        root.raise()
        root.requestActivate()
        sidebar.focusPageList()
    }

    function showPage(pageId) {
        root.showWindow()
        const index = pageCatalog.indexOf(pageId)
        if (index < 0)
            return
        sidebar.clearSearch()
        root.currentPage = index
    }

    SettingsDraft {
        id: optionsDraft
        onValuesChanged: root.refresh()
    }

    SettingsPages { id: pageCatalog }

    Shortcut {
        sequences: [StandardKey.Find]
        onActivated: sidebar.focusSearch()
    }

    Shortcut {
        sequences: [StandardKey.Cancel]
        onActivated: root.discardChanges()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            SettingsSidebar {
                id: sidebar
                catalog: pageCatalog
                currentPage: root.currentPage
                onPageRequested: function(page) { root.currentPage = page }
            }

            Kirigami.Separator { Layout.fillHeight: true }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 0

                SettingsPageHeader {
                    pageId: pageCatalog.pages[root.currentPage].id
                    title: pageCatalog.pages[root.currentPage].title
                    generalTab: root.generalTab
                    passwordsTab: root.passwordsTab
                    onGeneralTabSelected: function(index) { root.generalTab = index }
                    onPasswordsTabSelected: function(index) { root.passwordsTab = index }
                }

                SettingsPageStack {
                    draft: optionsDraft
                    catalog: pageCatalog
                    tabModel: root.tabModel
                    currentIndex: root.currentPage
                    generalTab: root.generalTab
                    passwordsTab: root.passwordsTab
                }
            }
        }

        SettingsButtonBar {
            modified: root.modified
            defaultsEnabled: root.defaultsEnabled
            onDefaultsClicked: root.restoreDefaults()
            onOkClicked: root.acceptAndClose()
            onApplyClicked: root.applyChanges()
            onCancelClicked: root.discardChanges()
        }
    }
}
