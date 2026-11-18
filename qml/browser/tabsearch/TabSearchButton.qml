import QtQuick
import QtQuick.Controls

ToolButton {
    display: AbstractButton.IconOnly
    icon.name: "go-down-search"
    icon.width: 16
    icon.height: 16
    ToolTip.visible: hovered
    ToolTip.text: qsTr("Search Tabs")
    ToolTip.delay: 600
    Accessible.name: ToolTip.text
}
