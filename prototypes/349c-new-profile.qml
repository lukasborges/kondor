// #349 Multiple profiles — "New Profile" dialog over the Manage Profiles window:
// a name and one of eight icons. "Edit Profile" is the same dialog with "Save".
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    width: 520
    height: 560
    color: Kirigami.Theme.backgroundColor

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.3)
    }

    Dialog {
        id: dialog
        popupType: Popup.Item
        closePolicy: Popup.NoAutoClose
        modal: false
        anchors.centerIn: parent
        title: "New Profile"

        contentItem: Kirigami.FormLayout {
            TextField {
                Kirigami.FormData.label: "Name:"
                text: "Shopping"
                focus: true
            }
            RowLayout {
                Kirigami.FormData.label: "Icon:"
                spacing: Kirigami.Units.smallSpacing
                ButtonGroup { id: icons }
                Repeater {
                    model: ["im-user", "go-home", "view-pim-tasks", "globe", "favorite", "games-config-board", "code-context", "flag"]
                    delegate: ToolButton {
                        required property string modelData
                        required property int index
                        icon.name: modelData
                        display: AbstractButton.IconOnly
                        checkable: true
                        checked: index === 3
                        ButtonGroup.group: icons
                    }
                }
            }
        }

        footer: DialogButtonBox {
            Button {
                text: "Create"
                icon.name: "list-add"
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Button {
                text: "Cancel"
                icon.name: "dialog-cancel"
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
    }

    Component.onCompleted: dialog.open()
}
