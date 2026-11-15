// Fake sign-in page used by the password prototypes (#191).
import QtQuick
import QtQuick.Layouts

Rectangle {
    anchors.fill: parent
    color: "#ffffff"
    ColumnLayout {
        anchors.centerIn: parent
        width: 340
        spacing: 12
        Text { text: "Sign in"; font.pixelSize: 22; font.bold: true; color: "#232629"; Layout.alignment: Qt.AlignHCenter }
        Text { text: "Email or phone"; color: "#31363b" }
        Rectangle { Layout.fillWidth: true; height: 34; radius: 4; border.color: "#bdc3c7"; color: "#fcfcfc" }
        Rectangle { Layout.preferredWidth: 90; height: 36; radius: 4; color: "#3daee9"; Layout.alignment: Qt.AlignRight
            Text { anchors.centerIn: parent; text: "Next"; color: "white"; font.bold: true } }
    }
}
