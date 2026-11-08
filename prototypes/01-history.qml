// #1 Browsing history — "History" window (Ctrl+H): search, grouped by day, context menu.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    id: root
    width: 760
    height: 600
    color: Kirigami.Theme.backgroundColor

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        ToolBar {
            Layout.fillWidth: true
            RowLayout {
                anchors.fill: parent
                Kirigami.SearchField { Layout.fillWidth: true; placeholderText: "Search history…" }
                ToolButton { text: "Clear History…"; icon.name: "edit-clear-history" }
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Kirigami.Theme.colorSet: Kirigami.Theme.View
            Kirigami.Theme.inherit: false
            background: Rectangle { color: Kirigami.Theme.backgroundColor }
            ListView {
                id: list
                clip: true
                section.property: "day"
                section.delegate: Kirigami.ListSectionHeader { required property string section; width: ListView.view.width; text: section }
                model: ListModel {
                    ListElement { day: "Today"; time: "14:32"; title: "KDE Community"; url: "https://kde.org/" }
                    ListElement { day: "Today"; time: "14:10"; title: "Plasma 6.5 — Release notes"; url: "https://kde.org/announcements/plasma/6/6.5.0/" }
                    ListElement { day: "Today"; time: "11:47"; title: "KDE – Wikipedia, the free encyclopedia"; url: "https://pt.wikipedia.org/wiki/KDE" }
                    ListElement { day: "Yesterday"; time: "21:05"; title: "Qt WebEngine Overview | Qt 6"; url: "https://doc.qt.io/qt-6/qtwebengine-overview.html" }
                    ListElement { day: "Yesterday"; time: "20:58"; title: "Kirigami — KDE Developer"; url: "https://develop.kde.org/frameworks/kirigami/" }
                    ListElement { day: "Yesterday"; time: "09:12"; title: "Planet KDE"; url: "https://planet.kde.org/" }
                    ListElement { day: "Tuesday, November 4, 2026"; time: "18:20"; title: "KDE Human Interface Guidelines"; url: "https://develop.kde.org/hig/" }
                }
                delegate: ItemDelegate {
                    required property string time
                    required property string title
                    required property string url
                    required property int index
                    width: ListView.view.width
                    highlighted: index === 1
                    contentItem: RowLayout {
                        spacing: Kirigami.Units.largeSpacing
                        Label { text: time; color: Kirigami.Theme.disabledTextColor; Layout.preferredWidth: 44 }
                        Kirigami.Icon { source: "internet-web-browser"; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
                        Label { text: title; elide: Text.ElideRight; Layout.maximumWidth: 330 }
                        Label { text: url; elide: Text.ElideRight; color: highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.disabledTextColor; Layout.fillWidth: true }
                    }
                }
            }
        }
    }

    Menu {
        popupType: Popup.Item
        x: 300
        y: 150
        MenuItem { text: "Open"; icon.name: "go-jump" }
        MenuItem { text: "Open in New Tab"; icon.name: "tab-new" }
        MenuItem { text: "Open in New Private Tab"; icon.name: "view-private" }
        MenuSeparator {}
        MenuItem { text: "Copy Address"; icon.name: "edit-copy" }
        MenuItem { text: "Add to Bookmarks"; icon.name: "bookmark-new" }
        MenuSeparator {}
        MenuItem { text: "Remove from History"; icon.name: "edit-delete" }
        Component.onCompleted: open()
    }
}
