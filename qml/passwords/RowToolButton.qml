import QtQuick.Controls

ToolButton {
    display: AbstractButton.IconOnly
    ToolTip.visible: hovered
    ToolTip.text: text
    ToolTip.delay: 600
}
