// #409 HTTPS-only mode: the site has no secure version, so Kondor stops before loading it over HTTP.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    address: "http://neverssl.com/"
    tabs: [{ title: "Secure site not available", icon: "security-medium" }]
    addressLeft: [
        ToolButton {
            icon.name: "security-medium"; text: "Not Secure"
            display: AbstractButton.TextBesideIcon; flat: true; implicitHeight: 28
            icon.color: Kirigami.Theme.neutralTextColor
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
            Kirigami.Icon { source: "security-medium"; Layout.preferredWidth: 96; Layout.preferredHeight: 96; Layout.alignment: Qt.AlignHCenter }
            Kirigami.Heading { level: 1; text: "Secure site not available"; Layout.alignment: Qt.AlignHCenter }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                text: "<b>neverssl.com</b> does not support HTTPS. Anyone on the network could see or change what is sent to it."
            }
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: Kirigami.Units.largeSpacing
                Button { text: "Continue to HTTP Site"; flat: true }
                Button { text: "Go Back"; icon.name: "go-previous"; highlighted: true }
            }
        }
    }
}
