import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import Kondor

Rectangle {
    id: root

    required property Tab tab

    default property alias page: viewport.data

    readonly property TabResponsive responsive: tab.responsive
    readonly property bool isResponsive: responsive.isActive
    readonly property real margin: Kirigami.Units.largeSpacing * 2
    readonly property real footer: Kirigami.Units.gridUnit * 2
    readonly property real fitScale: isResponsive && responsive.zoomToFit ? scaleToFit() : 1

    function scaleToFit() {
        const horizontal = (width - 2 * margin) / responsive.width
        const vertical = (height - margin - footer) / responsive.height
        return Math.max(0.1, Math.min(1, horizontal, vertical))
    }

    color: isResponsive
        ? Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.08)
        : "transparent"

    Flickable {
        id: scroller
        anchors.fill: parent
        clip: true
        interactive: false
        contentWidth: root.isResponsive ? Math.max(width, frame.width + 2 * root.margin) : width
        contentHeight: root.isResponsive ? frame.y + frame.height + root.footer : height
        ScrollBar.vertical: ScrollBar {}
        ScrollBar.horizontal: ScrollBar {}

        Item {
            id: frame
            x: Math.max(0, (scroller.contentWidth - width) / 2)
            y: root.isResponsive ? root.margin : 0
            width: root.isResponsive ? root.responsive.width * root.fitScale : scroller.width
            height: root.isResponsive ? root.responsive.height * root.fitScale : scroller.height

            Item {
                id: viewport
                width: root.isResponsive ? root.responsive.width : frame.width
                height: root.isResponsive ? root.responsive.height : frame.height
                scale: root.fitScale
                transformOrigin: Item.TopLeft
            }

            Rectangle {
                anchors.fill: parent
                anchors.margins: -1
                visible: root.isResponsive
                color: "transparent"
                border.color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, Kirigami.Theme.frameContrast)
            }

            ResponsiveHandles {
                anchors.fill: parent
                visible: root.isResponsive
                responsive: root.responsive
                fitScale: root.fitScale
                isCentered: frame.x > 0
            }

            Label {
                anchors.top: parent.bottom
                anchors.topMargin: Kirigami.Units.largeSpacing
                anchors.horizontalCenter: parent.horizontalCenter
                visible: root.isResponsive && root.fitScale < 1
                text: qsTr("%1 %").arg(Math.round(root.fitScale * 100))
                color: Kirigami.Theme.disabledTextColor
            }
        }
    }
}
