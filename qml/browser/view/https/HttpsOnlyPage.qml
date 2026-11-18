import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: root

    required property Tab tab

    readonly property string host: tab.security.upgradedFrom.host

    Rectangle {
        anchors.fill: parent
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor

        ColumnLayout {
            anchors.centerIn: parent
            width: Math.min(parent.width - 2 * Kirigami.Units.gridUnit, 560)
            spacing: Kirigami.Units.largeSpacing * 2

            Kirigami.Icon {
                source: "security-medium"
                Layout.preferredWidth: 96
                Layout.preferredHeight: 96
                Layout.alignment: Qt.AlignHCenter
            }

            Kirigami.Heading {
                level: 1
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: qsTr("Secure site not available")
            }

            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                textFormat: Text.RichText
                text: qsTr("<b>%1</b> does not support HTTPS. Anyone on the network could see or change what is sent to it.").arg(root.host)
            }

            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: Kirigami.Units.largeSpacing

                Button {
                    text: qsTr("Continue to HTTP Site")
                    flat: true
                    onClicked: root.tab.security.continueToHttp()
                }

                Button {
                    text: qsTr("Go Back")
                    icon.name: "go-previous"
                    highlighted: true
                    onClicked: root.tab.security.leaveHttpsOnlyWarning()
                }
            }
        }
    }
}
