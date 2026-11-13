import QtQuick.Controls

ToolButton {
    display: AbstractButton.IconOnly
    ToolTip.visible: hovered
    Accessible.name: ToolTip.text
    ToolTip.text: text
    ToolTip.delay: 600
}
