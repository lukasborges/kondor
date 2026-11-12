import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ApplicationWindow {
    id: root
    width: 700
    height: 600
    //: %1 is the application name
    title: qsTr("History — %1").arg(Qt.application.displayName)
    visible: false

    required property TabModel tabModel

    onClosing: function(close) {
        close.accepted = false
        root.visible = false
        HistoryManager.model.active = false
    }

    function showWindow() {
        root.visible = true
        HistoryManager.model.active = true
        root.raise()
        root.requestActivate()
        searchField.forceActiveFocus()
    }

    function openInNewTab(url) {
        if (!url || url === "")
            return
        root.tabModel.addTab(false, url)
    }

    function openFirstResult() {
        searchDebounce.stop()
        HistoryManager.model.filter = searchField.text
        root.openInNewTab(HistoryManager.model.urlAt(0))
    }

    function acceptKey(event, action) {
        action()
        event.accepted = true
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        ToolBar {
            Layout.fillWidth: true

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 4
                anchors.rightMargin: 4
                spacing: 4

                Kirigami.SearchField {
                    id: searchField
                    Layout.fillWidth: true
                    placeholderText: qsTr("Search history…")
                    onTextChanged: searchDebounce.restart()

                    Keys.onDownPressed: function(event) { root.acceptKey(event, historyList.focusFirstEntry) }
                    Keys.onReturnPressed: function(event) { root.acceptKey(event, root.openFirstResult) }
                    Keys.onEnterPressed: function(event) { root.acceptKey(event, root.openFirstResult) }
                }

                ToolButton {
                    text: qsTr("Clear History…")
                    icon.name: "edit-clear-history"
                    onClicked: clearDialog.open()
                }
            }
        }

        HistoryList {
            id: historyList
            Layout.fillWidth: true
            Layout.fillHeight: true
            onOpenRequested: function(url) { root.openInNewTab(url) }
        }
    }

    Timer {
        id: searchDebounce
        interval: 200
        onTriggered: HistoryManager.model.filter = searchField.text
    }

    ClearHistoryDialog {
        id: clearDialog
    }
}
