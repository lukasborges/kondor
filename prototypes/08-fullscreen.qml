// #8 Fullscreen — vídeo em tela cheia (sem abas/barra) com o aviso "Pressione Esc".
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    showHeader: false
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        Rectangle {
            anchors.centerIn: parent
            width: parent.width; height: parent.width * 9 / 16
            gradient: Gradient {
                GradientStop { position: 0; color: "#1d2c3a" }
                GradientStop { position: 1; color: "#0d1117" }
            }
            Kirigami.Icon { anchors.centerIn: parent; source: "media-playback-start"; width: 96; height: 96; opacity: 0.8 }
        }
        // Barra do player (desenhada pelo site)
        Rectangle {
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
            height: 46
            color: "#cc000000"
            Rectangle { x: 16; y: 8; width: parent.width - 32; height: 4; radius: 2; color: "#55ffffff"
                Rectangle { width: parent.width * 0.35; height: 4; radius: 2; color: "#da4453" } }
            Text { x: 16; y: 20; text: "4:12 / 12:03"; color: "#ffffff"; font.pixelSize: 13 }
        }
    }

    // Aviso transitório (3 s) no topo
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 24
        width: hint.implicitWidth + 2 * Kirigami.Units.largeSpacing * 2
        height: hint.implicitHeight + Kirigami.Units.largeSpacing * 2
        radius: Kirigami.Units.cornerRadius
        Kirigami.Theme.colorSet: Kirigami.Theme.Complementary
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor
        opacity: 0.92
        RowLayout {
            id: hint
            anchors.centerIn: parent
            spacing: Kirigami.Units.largeSpacing
            Kirigami.Icon { source: "view-fullscreen"; Layout.preferredWidth: 22; Layout.preferredHeight: 22 }
            Label { text: "<b>youtube.com</b> está em tela cheia — pressione <b>Esc</b> para sair"; color: Kirigami.Theme.textColor }
        }
    }
}
