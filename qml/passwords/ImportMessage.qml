import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.InlineMessage {
    id: root

    required property ImportResult result

    readonly property bool canTrash: !root.result.failed && !root.result.trashed
                                     && !root.result.trashFailed

    function messageText() {
        if (root.result.failed)
            return qsTr("Some passwords could not be saved to KWallet.")
        if (root.result.trashed)
            return qsTr("“%1” was moved to the trash.").arg(root.result.name)
        return qsTr("Imported %n password(s) from “%1”. The file holds your passwords unencrypted: delete it when you no longer need it.", "", root.result.count).arg(root.result.name)
    }

    function resetVisibility() {
        if (visible)
            return
        root.result.done = false
        visible = Qt.binding(function() { return root.result.done })
    }

    Layout.fillWidth: true
    visible: root.result.done
    type: root.result.failed ? Kirigami.MessageType.Error : Kirigami.MessageType.Positive
    showCloseButton: true
    text: root.messageText()
    actions: [
        Kirigami.Action {
            visible: root.canTrash
            text: qsTr("Move File to Trash")
            icon.name: "user-trash"
            onTriggered: root.result.moveFileToTrash()
        }
    ]
    onVisibleChanged: root.resetVisibility()
}
