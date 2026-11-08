// #7 Site permissions — camera and microphone request (Kirigami.InlineMessage at the top of the page).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    address: "https://meet.jit.si/ReuniaoKDE"
    tabs: [{ title: "Jitsi Meet", icon: "camera-web" }]
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    belowHeader: [
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            position: Kirigami.InlineMessage.Position.Header
            visible: true
            type: Kirigami.MessageType.Information
            icon.name: "camera-web"
            text: "<b>meet.jit.si</b> wants to use your <b>camera</b> and <b>microphone</b>."
            actions: [
                Kirigami.Action { text: "Allow"; icon.name: "dialog-ok-apply" },
                Kirigami.Action { text: "Block"; icon.name: "dialog-cancel" }
            ]
        }
    ]
    Rectangle {
        anchors.fill: parent
        color: "#1d1f21"
        Column {
            anchors.centerIn: parent
            spacing: 18
            Kirigami.Icon { source: "camera-web"; width: 96; height: 96; anchors.horizontalCenter: parent.horizontalCenter; opacity: 0.6 }
            Text { text: "Waiting for camera access…"; color: "#eff0f1"; font.pixelSize: 18; anchors.horizontalCenter: parent.horizontalCenter }
        }
    }
}
