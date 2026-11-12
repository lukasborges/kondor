import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Dialog {
    id: root

    property string message
    property string acceptText
    property string acceptIcon
    property bool destructive: true

    anchors.centerIn: Overlay.overlay
    width: Kirigami.Units.gridUnit * 22
    modal: true
    dim: true
    closePolicy: Popup.CloseOnEscape

    contentItem: Label {
        text: root.message
        wrapMode: Text.WordWrap
    }

    footer: DialogButtonBox {
        objectName: "confirmButtons"
        Button {
            objectName: "acceptButton"
            text: root.acceptText
            icon.name: root.acceptIcon
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
        }
        Button {
            objectName: "cancelButton"
            text: qsTr("Cancel")
            icon.name: "dialog-cancel"
            focus: true
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
        }
    }

    onOpened: footer.contentChildren[1].forceActiveFocus()
}
