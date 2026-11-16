// Fake sign-up page used by the password generator prototypes (#260). The page itself is web
// content, so its colors are the site's, not the theme's.
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: page

    property bool passwordFocused: true
    readonly property alias passwordField: passwordField

    anchors.fill: parent
    color: "#ffffff"

    component FieldLabel: Text { color: "#31363b" }
    component Field: Rectangle {
        property bool focused: false
        Layout.fillWidth: true
        height: 34
        radius: 4
        border.color: focused ? "#3daee9" : "#bdc3c7"
        border.width: focused ? 2 : 1
        color: "#fcfcfc"
    }

    ColumnLayout {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 40
        width: 340
        spacing: 10
        Text { text: "Create your account"; font.pixelSize: 22; font.bold: true; color: "#232629"; Layout.alignment: Qt.AlignHCenter }
        FieldLabel { text: "Email" }
        Field { Text { anchors.verticalCenter: parent.verticalCenter; x: 10; text: "user.one@example.org"; color: "#232629" } }
        FieldLabel { text: "Password" }
        Field { id: passwordField; focused: page.passwordFocused }
        FieldLabel { text: "Confirm password" }
        Field {}
        Rectangle { Layout.fillWidth: true; height: 36; radius: 4; color: "#3daee9"; Layout.topMargin: 6
            Text { anchors.centerIn: parent; text: "Sign up"; color: "white"; font.bold: true } }
    }
}
