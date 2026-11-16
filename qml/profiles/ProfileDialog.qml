import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Dialog {
    id: root

    property string profileId: ""
    readonly property bool isNew: root.profileId === ""
    readonly property string nameError: UserProfiles.nameError(nameField.text, root.profileId)
    readonly property bool isRejectedName: root.nameError.length > 0
    readonly property bool showsNameError: isRejectedName && nameField.text.trim().length > 0

    signal profileSaved(string profileId, bool isNew)

    anchors.centerIn: Overlay.overlay
    modal: true
    dim: true
    closePolicy: Popup.CloseOnEscape
    title: root.isNew ? qsTr("New Profile") : qsTr("Edit Profile")

    function openForNew() {
        root.profileId = ""
        nameField.text = ""
        iconPicker.iconName = root.firstUnusedIcon()
        root.open()
    }

    function openForEdit(profile) {
        root.profileId = profile.id
        nameField.text = profile.name
        iconPicker.iconName = profile.iconName
        root.open()
    }

    function firstUnusedIcon() {
        const used = UserProfiles.profiles.map(profile => profile.iconName)
        const free = UserProfiles.iconNames().filter(name => !used.includes(name))
        return free.length > 0 ? free[0] : "im-user"
    }

    function confirm() {
        if (root.isRejectedName)
            return
        if (root.isNew)
            root.profileId = UserProfiles.createProfile(nameField.text, iconPicker.iconName)
        else
            UserProfiles.editProfile(root.profileId, nameField.text, iconPicker.iconName)
        root.profileSaved(root.profileId, root.isNew)
        root.close()
    }

    onOpened: {
        nameField.forceActiveFocus()
        if (!root.isNew)
            nameField.selectAll()
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.FormLayout {
            TextField {
                id: nameField
                objectName: "nameField"
                Kirigami.FormData.label: qsTr("Name:")
                maximumLength: 64
                onAccepted: root.confirm()
            }
            ProfileIconPicker {
                id: iconPicker
                Kirigami.FormData.label: qsTr("Icon:")
            }
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: root.showsNameError
            type: Kirigami.MessageType.Error
            text: root.nameError
        }
    }

    footer: DialogButtonBox {
        Button {
            text: root.isNew ? qsTr("Create") : qsTr("Save")
            icon.name: root.isNew ? "list-add" : "document-save"
            enabled: !root.isRejectedName
            DialogButtonBox.buttonRole: DialogButtonBox.ActionRole
            onClicked: root.confirm()
        }
        Button {
            text: qsTr("Cancel")
            icon.name: "dialog-cancel"
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
        }
    }
}
