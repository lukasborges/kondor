import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ToolbarPopup {
    id: root

    required property var browserWindow
    property var results: []
    property bool isBeside: false

    function refresh() {
        results = WindowManager.searchTabs(browserWindow, field.text)
        list.selectFirstOtherTab()
    }

    function refreshKeepingSelection() {
        const selected = list.currentIndex
        results = WindowManager.searchTabs(browserWindow, field.text)
        list.currentIndex = Math.min(selected, results.length - 1)
    }

    function openFor(anchor, beside) {
        parent = anchor
        isBeside = beside
        field.clear()
        refresh()
        open()
    }

    function closeSelected() {
        list.closeSelected()
    }

    function choose(tab) {
        close()
        WindowManager.showSearchedTab(tab)
    }

    function closeTab(tab) {
        WindowManager.closeSearchedTab(tab)
        Qt.callLater(refreshKeepingSelection)
    }

    popupType: Popup.Item
    width: Kirigami.Units.gridUnit * 24
    padding: Kirigami.Units.smallSpacing
    x: isBeside ? parent.width : parent.width - width
    y: isBeside ? parent.height - height : parent.height
    onOpened: field.forceActiveFocus()

    Shortcut {
        sequence: "Ctrl+W"
        enabled: root.opened
        onActivated: root.closeSelected()
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.smallSpacing

        Kirigami.SearchField {
            id: field
            Layout.fillWidth: true
            placeholderText: qsTr("Search tabs")
            onTextChanged: root.refresh()
            onAccepted: list.chooseSelected()
            Keys.onDownPressed: list.moveSelection(1)
            Keys.onUpPressed: list.moveSelection(-1)
        }

        TabSearchList {
            id: list
            visible: count > 0
            showsSections: !root.browserWindow.privateWindow
            model: root.results
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(contentHeight,
                root.hostWindow.height * 0.7 - field.height - Kirigami.Units.gridUnit * 2)
            onTabChosen: tab => root.choose(tab)
            onTabCloseRequested: tab => root.closeTab(tab)
        }

        Kirigami.PlaceholderMessage {
            visible: list.count === 0
            text: qsTr("No matching tabs")
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.largeSpacing
        }
    }
}
