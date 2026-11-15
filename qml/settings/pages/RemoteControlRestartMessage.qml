import QtQuick
import org.kde.kirigami as Kirigami
import Kondor

Kirigami.InlineMessage {
    readonly property bool isSavedOn: Settings.remoteControlEnabled
    readonly property bool isPortChanged: isSavedOn && RemoteControl.active
        && Settings.remoteControlPort !== RemoteControl.port
    readonly property bool isHiddenForCommandLine: RemoteControl.requestedOnCommandLine && !isSavedOn

    type: Kirigami.MessageType.Information
    visible: !isHiddenForCommandLine && (isSavedOn !== RemoteControl.active || isPortChanged)
    text: qsTr("Restart Kondor to apply the remote control change.")
}
