// #9 Certificate error — page overlaid on the WebEngineView with "Back" and an advanced option.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    address: "https://expired.badssl.com/"
    tabs: [{ title: "Privacy error", icon: "security-low" }]
    addressLeft: [
        ToolButton {
            icon.name: "security-low"; text: "Not Secure"
            display: AbstractButton.TextBesideIcon; flat: true; implicitHeight: 28
            icon.color: Kirigami.Theme.negativeTextColor
        }
    ]
    Rectangle {
        anchors.fill: parent
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor

        ColumnLayout {
            anchors.centerIn: parent
            width: 560
            spacing: Kirigami.Units.largeSpacing * 2
            Kirigami.Icon { source: "security-low"; Layout.preferredWidth: 96; Layout.preferredHeight: 96; Layout.alignment: Qt.AlignHCenter }
            Kirigami.Heading { level: 1; text: "Your connection is not private"; Layout.alignment: Qt.AlignHCenter }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                text: "Attackers might be trying to steal your information from <b>expired.badssl.com</b> (for example, passwords, messages or credit cards)."
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                color: Kirigami.Theme.disabledTextColor
                text: "The server's certificate has expired. (ERR_CERT_DATE_INVALID)"
            }
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: Kirigami.Units.largeSpacing
                Button { text: "Advanced…"; flat: true; icon.name: "arrow-down" }
                Button { text: "Back to Safety"; icon.name: "go-previous"; highlighted: true }
            }
            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: true
                type: Kirigami.MessageType.Warning
                text: "This site could not prove its identity. Continuing may expose your data."
                actions: [ Kirigami.Action { text: "Continue Anyway (Unsafe)"; icon.name: "go-next" } ]
            }
        }
    }
}
