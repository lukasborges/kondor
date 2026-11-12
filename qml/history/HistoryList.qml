pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ScrollView {
    id: root

    signal openRequested(string url)

    function focusFirstEntry() {
        listView.currentIndex = 0
        listView.forceActiveFocus()
    }

    function isSingleClickActivation() {
        return Qt.styleHints["singleClickActivation"] === true
    }

    function selectEntry(index) {
        listView.currentIndex = index
        listView.forceActiveFocus()
    }

    function handleClick(entry, mouse) {
        if (mouse.button === Qt.RightButton)
            return entryMenu.popupFor(entry, mouse.x, mouse.y)
        root.selectEntry(entry.index)
        if (root.isSingleClickActivation())
            root.openRequested(entry.url)
    }

    function openCurrentEntry() {
        root.openRequested(HistoryManager.model.urlAt(listView.currentIndex))
    }

    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    background: Rectangle { color: Kirigami.Theme.backgroundColor }

    ListView {
        id: listView
        clip: true
        model: HistoryManager.model
        focus: true
        keyNavigationEnabled: true

        Keys.onReturnPressed: root.openCurrentEntry()
        Keys.onEnterPressed: root.openCurrentEntry()

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
                        root.openRequested(entry.url)
                }
                onClicked: function(mouse) { root.handleClick(entry, mouse) }
            }
        }
    }

    HistoryEntryMenu {
        id: entryMenu
        onOpenRequested: function(url) { root.openRequested(url) }
    }
}
