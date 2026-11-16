import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kondor

ToolButton {
    id: button

    required property Tab tab

    property color iconColor: palette.buttonText

    readonly property bool isMuted: tab.audio.isMuted

    Layout.preferredWidth: 20
    Layout.preferredHeight: 20
    flat: true
    display: AbstractButton.IconOnly
    icon.name: isMuted ? "audio-volume-muted-symbolic" : "audio-volume-high-symbolic"
    icon.color: iconColor
    icon.width: 16
    icon.height: 16
    ToolTip.visible: hovered
    ToolTip.text: isMuted ? qsTr("Unmute Tab") : qsTr("Mute Tab")
    ToolTip.delay: 600
    Accessible.name: ToolTip.text
    onClicked: tab.audio.toggleMuted()
}
