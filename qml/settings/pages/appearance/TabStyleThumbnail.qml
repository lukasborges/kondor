import QtQuick
import org.kde.kirigami as Kirigami

Rectangle {
    id: thumbnail

    property string tabStyle: "floating"

    readonly property bool isBelowAddressBar: tabStyle === "below"
    readonly property bool isSideBar: tabStyle === "vertical"

    width: Kirigami.Units.gridUnit * 8
    height: Kirigami.Units.gridUnit * 5
    radius: Kirigami.Units.cornerRadius
    color: Kirigami.Theme.backgroundColor
    border.color: Qt.alpha(Kirigami.Theme.textColor, 0.2)
    clip: true
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false

    Item {
        id: headerColors
        Kirigami.Theme.colorSet: Kirigami.Theme.Header
        Kirigami.Theme.inherit: false
        readonly property color backgroundColor: Kirigami.Theme.backgroundColor
    }

    Item {
        id: windowColors
        Kirigami.Theme.colorSet: Kirigami.Theme.Window
        Kirigami.Theme.inherit: false
        readonly property color backgroundColor: Kirigami.Theme.backgroundColor
    }

    Column {
        anchors.fill: parent
        anchors.margins: 1

        Rectangle {
            visible: !thumbnail.isBelowAddressBar && !thumbnail.isSideBar
            width: parent.width
            height: 14
            color: headerColors.backgroundColor

            ThumbnailTabs {
                x: 4
                y: 3
                tabStyle: thumbnail.tabStyle
                stripColor: headerColors.backgroundColor
                toolBarColor: windowColors.backgroundColor
            }
        }

        Rectangle {
            width: parent.width
            height: 12
            color: windowColors.backgroundColor

            Rectangle {
                x: 18
                y: 3
                width: parent.width - 26
                height: 6
                radius: 2
                color: thumbnail.color
                border.color: Qt.alpha(Kirigami.Theme.textColor, 0.25)
            }
        }

        Rectangle {
            visible: thumbnail.isBelowAddressBar
            width: parent.width
            height: 13
            color: windowColors.backgroundColor

            ThumbnailTabs {
                x: 4
                y: 2
                tabStyle: thumbnail.tabStyle
                stripColor: windowColors.backgroundColor
                toolBarColor: windowColors.backgroundColor
            }
        }

        ThumbnailSideBar {
            visible: thumbnail.isSideBar
            height: thumbnail.height - 16
            color: windowColors.backgroundColor
        }
    }
}
