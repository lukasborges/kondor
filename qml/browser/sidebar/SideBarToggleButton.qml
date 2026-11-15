import QtQuick
import QtQuick.Controls
import Kondor

ToolButton {
    id: button

    readonly property bool isRightToLeft: Qt.application.layoutDirection === Qt.RightToLeft
    readonly property string edge: isRightToLeft ? "right" : "left"

    display: AbstractButton.IconOnly
    icon.name: (Settings.sideBarCollapsed ? "sidebar-expand-" : "sidebar-collapse-") + edge
    text: Settings.sideBarCollapsed ? qsTr("Expand Side Bar") : qsTr("Collapse Side Bar")
    ToolTip.visible: hovered
    ToolTip.text: text
    ToolTip.delay: 600
    Accessible.name: text
    onClicked: Settings.sideBarCollapsed = !Settings.sideBarCollapsed
}
