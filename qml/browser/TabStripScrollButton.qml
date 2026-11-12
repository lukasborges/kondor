import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ToolButton {
    required property var tabStrip

    visible: tabStrip.overflowing
    Layout.preferredWidth: visible ? implicitWidth : 0
    Layout.alignment: Qt.AlignVCenter
    autoRepeat: true
    display: AbstractButton.IconOnly
    icon.width: 16
    icon.height: 16
    ToolTip.visible: hovered
    ToolTip.delay: 600
}
