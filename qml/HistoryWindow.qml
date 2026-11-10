pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// "History" window (Ctrl+H): search, grouped by day, context menu.
// Created on demand in BrowserWindow.qml. Visuals follow the 01-history.qml prototype.
ApplicationWindow {
    id: root
    width: 700
    height: 600
    //: %1 is the application name
    title: qsTr("History — %1").arg(Qt.application.displayName)
    visible: false

    required property TabModel tabModel

    onClosing: function(close) {
        // Do not destroy: just hide, so it reopens quickly.
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

    // Applies a pending search immediately, so Enter never opens a stale result.
    function openFirstResult() {
        searchDebounce.stop()
        HistoryManager.model.filter = searchField.text
        root.openInNewTab(HistoryManager.model.urlAt(0))
    }

    // Copies via a hidden TextEdit (the simple way to reach the clipboard in QML).
    TextEdit {
        id: clipboardHelper
        visible: false
    }

    function copyAddress(text) {
        clipboardHelper.text = text
        clipboardHelper.selectAll()
        clipboardHelper.copy()
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

                    Keys.onDownPressed: function(event) {
                        listView.currentIndex = 0
                        listView.forceActiveFocus()
                        event.accepted = true
                    }
                    Keys.onReturnPressed: function(event) {
                        root.openFirstResult()
                        event.accepted = true
                    }
                    Keys.onEnterPressed: function(event) {
                        root.openFirstResult()
                        event.accepted = true
                    }
                }

                ToolButton {
                    text: qsTr("Clear History…")
                    icon.name: "edit-clear-history"
                    onClicked: clearDialog.open()
                }
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Kirigami.Theme.colorSet: Kirigami.Theme.View
            Kirigami.Theme.inherit: false
            background: Rectangle { color: Kirigami.Theme.backgroundColor }

            ListView {
                id: listView
                clip: true
                model: HistoryManager.model
                focus: true
                keyNavigationEnabled: true

                Keys.onReturnPressed: root.openInNewTab(HistoryManager.model.urlAt(listView.currentIndex))
                Keys.onEnterPressed: root.openInNewTab(HistoryManager.model.urlAt(listView.currentIndex))

                section.property: "dayLabel"
                section.delegate: Kirigami.ListSectionHeader {
                    required property string section
                    width: ListView.view.width
                    text: section
                }

                delegate: ItemDelegate {
                    id: entry
                    required property int index
                    required property int id
                    required property string url
                    required property string title
                    required property string time

                    width: ListView.view.width
                    highlighted: ListView.isCurrentItem

                    contentItem: RowLayout {
                        spacing: Kirigami.Units.largeSpacing

                        Label {
                            text: entry.time
                            color: Kirigami.Theme.disabledTextColor
                            Layout.preferredWidth: 44
                        }

                        Kirigami.Icon {
                            source: "internet-web-browser"
                            Layout.preferredWidth: 16
                            Layout.preferredHeight: 16
                        }

                        Label {
                            text: entry.title.length ? entry.title : entry.url
                            elide: Text.ElideRight
                            font.bold: true
                            Layout.maximumWidth: 330
                        }

                        Label {
                            text: entry.url
                            elide: Text.ElideRight
                            color: entry.highlighted
                                   ? Kirigami.Theme.highlightedTextColor
                                   : Kirigami.Theme.disabledTextColor
                            Layout.fillWidth: true
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.LeftButton | Qt.RightButton

                        onDoubleClicked: function(mouse) {
                            if (mouse.button === Qt.LeftButton)
                                root.openInNewTab(entry.url)
                        }
                        onClicked: function(mouse) {
                            if (mouse.button === Qt.RightButton) {
                                entryMenu.entryUrl = entry.url
                                entryMenu.entryId = entry.id
                                entryMenu.popup(entry, mouse.x, mouse.y)
                                return
                            }
                            listView.currentIndex = entry.index
                            listView.forceActiveFocus()
                            // Qt.styleHints is typed QObject* in the QML global
                            // object, but returns a QStyleHints at runtime.
                            // qmllint disable missing-property
                            if (Qt.styleHints.singleClickActivation)
                                root.openInNewTab(entry.url)
                        }
                    }
                }
            }
        }
    }

    Timer {
        id: searchDebounce
        interval: 200
        onTriggered: HistoryManager.model.filter = searchField.text
    }

    Menu {
        id: entryMenu
        property string entryUrl: ""
        property int entryId: -1

        MenuItem {
            text: qsTr("Open in New Tab")
            icon.name: "tab-new"
            onTriggered: root.openInNewTab(entryMenu.entryUrl)
        }
        MenuItem {
            text: qsTr("Copy Address")
            icon.name: "edit-copy"
            onTriggered: root.copyAddress(entryMenu.entryUrl)
        }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Remove from History")
            icon.name: "edit-delete"
            onTriggered: HistoryManager.removeEntry(entryMenu.entryId)
        }
    }

    Dialog {
        id: clearDialog
        title: qsTr("Clear History")
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        anchors.centerIn: parent

        ColumnLayout {
            spacing: 8

            Label {
                text: qsTr("Remove from history:")
            }

            ComboBox {
                id: rangeBox
                model: [qsTr("Last hour"), qsTr("Today"), qsTr("Everything")]
            }
        }

        onAccepted: {
            const now = Date.now()
            if (rangeBox.currentIndex === 0) {
                HistoryManager.clearSince(now - 3600 * 1000)
            } else if (rangeBox.currentIndex === 1) {
                const d = new Date()
                d.setHours(0, 0, 0, 0)
                HistoryManager.clearSince(d.getTime())
            } else {
                HistoryManager.clearAll()
            }
        }
    }
}
