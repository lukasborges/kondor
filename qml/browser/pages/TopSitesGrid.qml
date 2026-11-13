pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

GridLayout {
    id: root

    required property var sites
    required property real contentWidth

    signal navigateRequested(string url)
    signal openInNewTabRequested(string url)
    signal menuRequested(var request)

    columns: Math.max(1, Math.min(4,
        Math.floor(root.contentWidth / (Kirigami.Units.gridUnit * 8))))
    rowSpacing: Kirigami.Units.largeSpacing
    columnSpacing: Kirigami.Units.largeSpacing

    function activate(url) {
        if (BookmarkManager.ctrlPressed())
            root.openInNewTabRequested(url)
        else
            root.navigateRequested(url)
    }

    function handleSecondaryClick(site, tile, mouse) {
        if (mouse.button === Qt.MiddleButton)
            root.openInNewTabRequested(site.url)
        else
            root.menuRequested({ site: site, tile: tile, x: mouse.x, y: mouse.y })
    }

    Repeater {
        model: root.sites

        delegate: ItemDelegate {
            id: tile
            required property var modelData

            Layout.preferredWidth: Kirigami.Units.gridUnit * 7
            Layout.maximumWidth: Kirigami.Units.gridUnit * 7
            Accessible.name: tile.modelData.host

            contentItem: ColumnLayout {
                spacing: Kirigami.Units.smallSpacing

                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: Kirigami.Units.gridUnit * 3.5
                    Layout.preferredHeight: Kirigami.Units.gridUnit * 3.5
                    radius: Kirigami.Units.cornerRadius
                    color: Kirigami.Theme.alternateBackgroundColor
                    border.color: Qt.alpha(Kirigami.Theme.textColor, 0.15)

                    SiteIcon {
                        anchors.centerIn: parent
                        width: Kirigami.Units.iconSizes.medium
                        height: width
                        pageUrl: tile.modelData.url
                        fallback: "internet-web-browser"
                    }
                }

                Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    text: tile.modelData.host
                }
            }

            ToolTip.visible: hovered
            ToolTip.text: tile.modelData.title.length
                          ? tile.modelData.title + "\n" + tile.modelData.url
                          : tile.modelData.url
            ToolTip.delay: 600

            Accessible.role: Accessible.ListItem
            Accessible.onPressAction: root.activate(tile.modelData.url)
            onClicked: root.activate(tile.modelData.url)

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.MiddleButton | Qt.RightButton
                onClicked: function(mouse) { root.handleSecondaryClick(tile.modelData, tile, mouse) }
            }
        }
    }
}
