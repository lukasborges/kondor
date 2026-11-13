import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Dialog {
    id: root

    property var targetId: -1
    property bool targetIsFolder: true
    property string targetTitle: ""

    readonly property bool hasName: renameField.text.trim().length > 0

    title: root.targetIsFolder ? qsTr("Rename Folder") : qsTr("Rename Bookmark")
    standardButtons: Dialog.Ok | Dialog.Cancel
    modal: true
    anchors.centerIn: parent

    onOpened: root.prepareField()
    onAccepted: root.renameTarget()
    Component.onCompleted: standardButton(Dialog.Ok).enabled = Qt.binding(() => root.hasName)

    function openFor(target, isFolder) {
        if (!target.id)
            return
        root.targetId = target.id
        root.targetIsFolder = isFolder
        root.targetTitle = target.title
        root.open()
    }

    function prepareField() {
        renameField.text = root.targetTitle
        renameField.selectAll()
        renameField.forceActiveFocus()
    }

    function renameTarget() {
        if (root.targetId > 0)
            BookmarkManager.rename(root.targetId, renameField.text)
    }

    ColumnLayout {
        spacing: Kirigami.Units.smallSpacing

        Label {
            text: qsTr("New name:")
        }

        TextField {
            id: renameField
            Layout.fillWidth: true
            Layout.preferredWidth: Kirigami.Units.gridUnit * 18
            onAccepted: {
                if (root.hasName)
                    root.accept()
            }
        }
    }
}
