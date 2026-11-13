import QtQuick
import Kondor

Connections {
    function notifyIfInBackground() {
        if (Qt.application.state === Qt.ApplicationActive)
            return
        const result = PasswordStore.claimImportNotification()
        if (result.fileName !== undefined)
            Notifier.notify(qsTr("Passwords Imported"),
                            qsTr("%n password(s) imported from %1", "", result.count).arg(result.fileName),
                            "dialog-password")
    }

    target: PasswordStore
    function onImportFinished() { notifyIfInBackground() }
}
