import QtQuick
import Kondor

Item {
    id: root

    required property TabModel tabs
    required property var browserWindow

    property bool quitConfirmed: false

    function handleClosing(close) {
        SessionManager.save(tabs)
        if (mustConfirmQuit()) {
            close.accepted = false
            quitDialog.open()
            return
        }
        WindowManager.closeWindow(browserWindow)
    }

    function mustConfirmQuit() {
        return WindowManager.windowCount <= 1 && DownloadManager.hasActiveDownloads
                && !quitConfirmed
    }

    ConfirmDialog {
        id: quitDialog
        //: %1 is the application name
        title: qsTr("Quit %1").arg(Qt.application.displayName)
        message: qsTr("Downloads are still in progress. Quit anyway?")
        acceptText: qsTr("Quit")
        acceptIcon: "application-exit"
        destructive: false
        onAccepted: {
            root.quitConfirmed = true
            root.browserWindow.close()
        }
    }
}
