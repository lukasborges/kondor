import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ApplicationWindow {
    id: root

    property string chosenProfileId: ""

    width: 380
    height: 340
    visible: true
    title: qsTr("Choose a Profile")

    function lastUsedIndex() {
        const index = UserProfiles.profiles.findIndex(profile => profile.id === UserProfiles.lastUsedProfileId)
        return Math.max(index, 0)
    }

    function choose(profile) {
        root.chosenProfileId = profile.id
        root.close()
    }

    Shortcut {
        sequence: "Escape"
        onActivated: root.close()
    }

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
                currentIndex: root.lastUsedIndex()
                Keys.onReturnPressed: root.choose(UserProfiles.profiles[currentIndex])
                Keys.onEnterPressed: root.choose(UserProfiles.profiles[currentIndex])
                delegate: ItemDelegate {
                    required property var modelData
                    width: ListView.view.width
                    highlighted: ListView.isCurrentItem
                    text: modelData.name
                    icon.name: modelData.iconName
                    icon.width: Kirigami.Units.iconSizes.smallMedium
                    icon.height: Kirigami.Units.iconSizes.smallMedium
                    onClicked: root.choose(modelData)
                }
            }
        }

        DialogButtonBox {
            Layout.fillWidth: true
            padding: 0
            Button {
                text: qsTr("Quit")
                icon.name: "application-exit"
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
            onRejected: root.close()
        }
    }
}
