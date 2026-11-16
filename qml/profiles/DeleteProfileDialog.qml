import QtQuick
import Kondor

ConfirmDialog {
    id: root

    property string profileId: ""
    property string profileName: ""

    title: qsTr("Delete Profile “%1”?").arg(root.profileName)
    message: qsTr("History, bookmarks, saved passwords, cookies, extensions and settings of this profile are deleted for good.")
    acceptText: qsTr("Delete")
    acceptIcon: "edit-delete"
    onAccepted: UserProfiles.deleteProfile(root.profileId)

    function openFor(profile) {
        root.profileId = profile.id
        root.profileName = profile.name
        root.open()
    }
}
