// #7 Site permissions — pedido de câmera e microfone (Kirigami.InlineMessage no topo da página).
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
            text: "<b>meet.jit.si</b> quer usar sua <b>câmera</b> e seu <b>microfone</b>."
            actions: [
                Kirigami.Action { text: "Permitir"; icon.name: "dialog-ok-apply" },
                Kirigami.Action { text: "Bloquear"; icon.name: "dialog-cancel" }
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
            Text { text: "Aguardando acesso à câmera…"; color: "#eff0f1"; font.pixelSize: 18; anchors.horizontalCenter: parent.horizontalCenter }
        }
    }
}
