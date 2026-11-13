import QtQuick
import QtQuick.Controls

ToolButton {
    id: root

    required property var modelData
    readonly property bool hasIconFile: modelData.iconSource.includes("/")

    display: AbstractButton.IconOnly
    icon.name: hasIconFile ? "" : modelData.iconSource
    icon.source: hasIconFile ? modelData.iconSource : ""
    icon.color: "transparent"
    ToolTip.visible: hovered
    ToolTip.text: modelData.name
    ToolTip.delay: 600
    Accessible.name: modelData.name
}
