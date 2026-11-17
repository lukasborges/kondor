import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Dialog {
    id: root

    property TabIdentity identity: null

    function initialText() {
        return root.identity.currentAgent || root.identity.defaultAgent
    }

    anchors.centerIn: Overlay.overlay
    width: Kirigami.Units.gridUnit * 36
    modal: true
    title: qsTr("Custom Browser Identity")
    standardButtons: Dialog.Ok | Dialog.Cancel

    onAboutToShow: agentField.text = root.initialText()
    onAccepted: root.identity.setAgent(agentField.text.trim())

    Component.onCompleted: standardButton(Dialog.Ok).enabled = Qt.binding(
        () => agentField.text.trim().length > 0)

    contentItem: Kirigami.FormLayout {
        Label {
            Kirigami.FormData.label: qsTr("Site:")
            text: root.identity ? root.identity.host : ""
        }

        TextArea {
            id: agentField
            Kirigami.FormData.label: qsTr("User agent:")
            Layout.preferredWidth: Kirigami.Units.gridUnit * 24
            wrapMode: TextEdit.WrapAnywhere
            selectByMouse: true
        }
    }
}
