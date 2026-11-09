// #43 New Tab page — what a new normal tab shows: logo + application name, a search/address
// field and the top sites from history. The tile menu (right click) is open on the third tile.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    tabs: [{ title: "KDE Community", icon: "kde" }, { title: "New Tab", icon: "tab-new" }]
    currentTab: 1
    address: ""
    addressFocused: true

    Rectangle {
        id: page
        anchors.fill: parent
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor

        ColumnLayout {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: Kirigami.Units.gridUnit * 4
            width: Math.min(parent.width - Kirigami.Units.gridUnit * 4, Kirigami.Units.gridUnit * 36)
            spacing: Kirigami.Units.gridUnit * 2

            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: Kirigami.Units.largeSpacing
                Kirigami.Icon { source: "kondor"; fallback: "internet-web-browser"; Layout.preferredWidth: 64; Layout.preferredHeight: 64 }
                Kirigami.Heading { level: 1; text: "Kondor Browser" }
            }

            TextField {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: Kirigami.Units.gridUnit * 30
                placeholderText: "Search or enter address"
            }

            GridLayout {
                id: grid
                Layout.alignment: Qt.AlignHCenter
                columns: 4
                rowSpacing: Kirigami.Units.largeSpacing
                columnSpacing: Kirigami.Units.largeSpacing

                Repeater {
                    model: [
                        { host: "kde.org", icon: "kde" },
                        { host: "en.wikipedia.org", icon: "internet-web-browser" },
                        { host: "github.com", icon: "internet-web-browser" },
                        { host: "fedoraproject.org", icon: "internet-web-browser" },
                        { host: "invent.kde.org", icon: "kde" },
                        { host: "planet.kde.org", icon: "kde" },
                        { host: "duckduckgo.com", icon: "internet-web-browser" },
                        { host: "news.ycombinator.com", icon: "internet-web-browser" }
                    ]
                    delegate: ItemDelegate {
                        id: tile
                        required property var modelData
                        required property int index
                        Layout.preferredWidth: Kirigami.Units.gridUnit * 7
                        highlighted: index === 2
                        contentItem: ColumnLayout {
                            spacing: Kirigami.Units.smallSpacing
                            Rectangle {
                                Layout.alignment: Qt.AlignHCenter
                                Layout.preferredWidth: Kirigami.Units.gridUnit * 3.5
                                Layout.preferredHeight: Kirigami.Units.gridUnit * 3.5
                                radius: Kirigami.Units.cornerRadius
                                color: Kirigami.Theme.alternateBackgroundColor
                                border.color: Qt.alpha(Kirigami.Theme.textColor, 0.15)
                                Kirigami.Icon {
                                    anchors.centerIn: parent
                                    width: Kirigami.Units.iconSizes.medium
                                    height: width
                                    source: tile.modelData.icon
                                }
                            }
                            Label {
                                Layout.fillWidth: true
                                horizontalAlignment: Text.AlignHCenter
                                elide: Text.ElideRight
                                text: tile.modelData.host
                            }
                        }
                    }
                }
            }
        }

        Menu {
            popupType: Popup.Item
            x: page.width / 2 + 10
            y: Kirigami.Units.gridUnit * 16
            MenuItem { text: "Open in New Tab"; icon.name: "tab-new" }
            MenuItem { text: "Open in New Private Tab"; icon.name: "view-private" }
            MenuSeparator {}
            MenuItem { text: "Remove from Top Sites"; icon.name: "list-remove" }
            Component.onCompleted: open()
        }
    }
}
