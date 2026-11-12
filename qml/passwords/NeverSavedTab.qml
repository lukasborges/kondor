import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ColumnLayout {
    spacing: Kirigami.Units.largeSpacing

    function removeSite(site) {
        Settings.passwordNeverSaveSites = Settings.passwordNeverSaveSites.filter(function(saved) {
            return saved !== site
        })
    }

    Label {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: qsTr("Kondor never offers to save passwords on these sites.")
    }

    PasswordsFrame {
        Layout.fillWidth: true
        Layout.fillHeight: true

        ListView {
            anchors.fill: parent
            clip: true
            model: Settings.passwordNeverSaveSites

            delegate: ItemDelegate {
                required property string modelData
                width: ListView.view.width

                contentItem: RowLayout {
                    Label {
                        text: modelData.replace(/^https?:[/][/]/, "")
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }

                    Button {
                        text: qsTr("Remove")
                        icon.name: "list-remove"
                        flat: true
                        onClicked: removeSite(modelData)
                    }
                }
            }
        }
    }
}
