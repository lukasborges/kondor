import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Item {
    id: root

    required property var tab
    required property bool zoomEnabled
    required property bool isFullScreen

    signal fullScreenToggled

    implicitWidth: zoomLayout.implicitWidth
    implicitHeight: zoomLayout.implicitHeight + 4

    RowLayout {
        id: zoomLayout
        anchors.fill: parent
        anchors.leftMargin: Kirigami.Units.largeSpacing + Kirigami.Units.iconSizes.small
                            + Kirigami.Units.smallSpacing * 2 + 2
        anchors.rightMargin: Kirigami.Units.smallSpacing
        spacing: 0

        Label {
            text: qsTr("Zoom")
            Layout.fillWidth: true
        }
        ToolButton {
            icon.name: "zoom-out"
            display: AbstractButton.IconOnly
            flat: true
            enabled: root.zoomEnabled
            ToolTip.visible: hovered
            Accessible.name: ToolTip.text
            ToolTip.text: qsTr("Zoom Out (Ctrl+−)")
            ToolTip.delay: 600
            onClicked: root.tab.zoomOut()
        }
        ToolButton {
            Layout.preferredWidth: Kirigami.Units.gridUnit * 3
            flat: true
            enabled: root.zoomEnabled
            text: (root.tab ? Math.round(root.tab.zoomFactor * 100) : 100) + "%"
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Reset Zoom (Ctrl+0)")
            ToolTip.delay: 600
            onClicked: root.tab.resetZoom()
        }
        ToolButton {
            icon.name: "zoom-in"
            display: AbstractButton.IconOnly
            flat: true
            enabled: root.zoomEnabled
            ToolTip.visible: hovered
            Accessible.name: ToolTip.text
            ToolTip.text: qsTr("Zoom In (Ctrl++)")
            ToolTip.delay: 600
            onClicked: root.tab.zoomIn()
        }
        Kirigami.Separator {
            Layout.fillHeight: true
            Layout.margins: 6
        }
        ToolButton {
            icon.name: root.isFullScreen ? "view-restore" : "view-fullscreen"
            display: AbstractButton.IconOnly
            flat: true
            ToolTip.visible: hovered
            Accessible.name: ToolTip.text
            ToolTip.text: root.isFullScreen ? qsTr("Exit Full Screen (F11)")
                                            : qsTr("Full Screen (F11)")
            ToolTip.delay: 600
            onClicked: root.fullScreenToggled()
        }
    }
}
