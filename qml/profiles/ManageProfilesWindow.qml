import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ApplicationWindow {
    id: root

    property int runningRevision: 0

    width: 520
    height: 560
    visible: false
    title: qsTr("Manage Profiles")

    function showWindow() {
        root.visible = true
        root.raise()
        root.requestActivate()
    }

    function startupIndex() {
        const index = UserProfiles.profiles.findIndex(profile => profile.id === UserProfiles.startupProfileId)
        return index + 1
    }

    function startupChoices() {
        return [qsTr("Ask Every Time")].concat(UserProfiles.profiles.map(profile => profile.name))
    }

    function chooseStartup(index) {
        UserProfiles.startupProfileId = index === 0 ? "" : UserProfiles.profiles[index - 1].id
    }

    Shortcut {
        sequence: "Escape"
        onActivated: root.close()
    }

    Timer {
        interval: 3000
        repeat: true
        running: root.visible
        onTriggered: root.runningRevision++
    }

    ProfileDialog { id: profileDialog }

    DeleteProfileDialog { id: deleteDialog }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.largeSpacing

        ProfileListFrame {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ListView {
                id: list
                clip: true
                focus: true
                model: UserProfiles.profiles
                Keys.onReturnPressed: profileDialog.openForEdit(UserProfiles.profiles[currentIndex])
                Keys.onEnterPressed: profileDialog.openForEdit(UserProfiles.profiles[currentIndex])
                delegate: ManageProfileRow {
                    runningRevision: root.runningRevision
                    onEditRequested: profile => profileDialog.openForEdit(profile)
                    onDeleteRequested: profile => deleteDialog.openFor(profile)
                }
            }
        }

        Button {
            text: qsTr("New Profile…")
            icon.name: "list-add"
            onClicked: profileDialog.openForNew()
        }

        Kirigami.FormLayout {
            Layout.fillWidth: true
            ComboBox {
                Kirigami.FormData.label: qsTr("At startup:")
                model: root.startupChoices()
                currentIndex: root.startupIndex()
                onActivated: index => root.chooseStartup(index)
            }
        }

        DialogButtonBox {
            Layout.fillWidth: true
            padding: 0
            standardButtons: DialogButtonBox.Close
            onRejected: root.close()
        }
    }
}
