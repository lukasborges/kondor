import QtQuick
import org.kde.kirigami as Kirigami
import Kondor

Kirigami.InlineMessage {
    id: root

    readonly property bool isSavedOn: Settings.remoteControlEnabled
    readonly property bool isPortChanged: isSavedOn && RemoteControl.active
        && Settings.remoteControlPort !== RemoteControl.port
    readonly property bool isHiddenForCommandLine: RemoteControl.requestedOnCommandLine && !isSavedOn

    function restartNow() {
        if (DownloadManager.hasActiveDownloads)
            restartDialog.open()
        else
            AppRestart.restart()
    }

    type: Kirigami.MessageType.Information
    visible: !isHiddenForCommandLine && (isSavedOn !== RemoteControl.active || isPortChanged)
    text: qsTr("Restart Kondor to apply the remote control change.")
    actions: Kirigami.Action {
        text: qsTr("Restart Now")
        icon.name: "view-refresh"
        onTriggered: root.restartNow()
    }

    ConfirmDialog {
        id: restartDialog
        //: %1 is the application name
        title: qsTr("Restart %1").arg(Qt.application.displayName)
        message: qsTr("Downloads are still in progress. Restart anyway?")
        acceptText: qsTr("Restart")
        acceptIcon: "view-refresh"
        destructive: false
        onAccepted: AppRestart.restart()
    }
}
