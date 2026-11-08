// #23 Spell checking — palavra sublinhada num campo de texto e sugestões no topo do menu de contexto.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    address: "https://invent.kde.org/lukasborges/kondor/-/issues/23"
    tabs: [{ title: "Spell checking (#23) · Kondor", icon: "kde" }]
    Rectangle {
        anchors.fill: parent
        color: "#ffffff"
        ColumnLayout {
            x: 80; y: 40
            width: 640
            spacing: 10
            Text { text: "Comentar"; font.pixelSize: 18; font.bold: true; color: "#232629" }
            Rectangle {
                Layout.fillWidth: true; height: 150; radius: 4; border.color: "#3daee9"; color: "#fcfcfc"
                Text {
                    x: 12; y: 12; width: parent.width - 24
                    wrapMode: Text.WordWrap; font.pixelSize: 15; color: "#232629"; textFormat: Text.RichText
                    text: "Testei a correção ortográfica e funcionou muito bem no <span style='text-decoration: underline; text-decoration-color: red; color:#232629'>navegaor</span>. Os dicionários em inglês e português foram carregados."
                }
                // Sublinhado ondulado simulado
                Canvas {
                    x: 430; y: 32; width: 72; height: 5
                    onPaint: { const c = getContext("2d"); c.strokeStyle = "#da4453"; c.lineWidth = 1.2; c.beginPath()
                        for (let i = 0; i <= width; i += 3) c.lineTo(i, (i / 3) % 2 ? 4 : 1); c.stroke() }
                }
            }
        }
    }

    Menu {
        popupType: Popup.Item
        x: 560
        y: 96
        MenuItem { text: "navegador"; font.bold: true }
        MenuItem { text: "navegado"; font.bold: true }
        MenuItem { text: "navegar"; font.bold: true }
        MenuSeparator {}
        MenuItem { text: "Desfazer"; icon.name: "edit-undo" }
        MenuItem { text: "Recortar"; icon.name: "edit-cut" }
        MenuItem { text: "Copiar"; icon.name: "edit-copy" }
        MenuItem { text: "Colar"; icon.name: "edit-paste" }
        MenuItem { text: "Selecionar tudo"; icon.name: "edit-select-all" }
        MenuSeparator {}
        Menu {
            title: "Idiomas da ortografia"
            icon.name: "tools-check-spelling"
            popupType: Popup.Item
            MenuItem { text: "Português (Brasil)"; checkable: true; checked: true }
            MenuItem { text: "English (US)"; checkable: true; checked: true }
        }
        Component.onCompleted: open()
    }
}
