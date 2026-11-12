import QtQuick
import QtQuick.Controls
import Kondor

ToolButton {
    id: root

    required property TabModel tabs

    readonly property real factor: tabs.currentTab ? tabs.currentTab.zoomFactor : 1.0

    visible: Math.round(factor * 100) !== 100
    text: Math.round(factor * 100) + "%"
    icon.name: "zoom-in"
    icon.width: 16
    icon.height: 16
    display: AbstractButton.TextBesideIcon
    flat: true
    implicitHeight: 28
    ToolTip.visible: hovered
    ToolTip.text: qsTr("Reset Zoom (Ctrl+0)")
    ToolTip.delay: 600
    onClicked: tabs.currentTab.resetZoom()
}
