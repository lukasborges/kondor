// #22 Reader mode — artigo limpo nas cores do tema KDE, botão marcado na barra e controles flutuantes.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    address: "https://blogs.kde.org/2026/10/plasma-6-5"
    tabs: [{ title: "Plasma 6.5: o que há de novo", icon: "internet-web-browser" }]
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    addressRight: [
        ToolButton { icon.name: "view-readermode"; display: AbstractButton.IconOnly; flat: true; checked: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    Rectangle {
        anchors.fill: parent
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor

        ColumnLayout {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 40
            width: 640
            spacing: 16
            Label { text: "BLOGS.KDE.ORG"; color: Kirigami.Theme.disabledTextColor; font.letterSpacing: 1.5; font.pointSize: Kirigami.Theme.smallFont.pointSize }
            Label { text: "Plasma 6.5: o que há de novo"; font.pixelSize: 32; font.family: "Noto Serif"; font.bold: true; Layout.fillWidth: true; wrapMode: Text.WordWrap }
            Label { text: "Por Equipe de Promoção do KDE · 7 min de leitura"; color: Kirigami.Theme.disabledTextColor }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                font.family: "Noto Serif"; font.pixelSize: 18; lineHeight: 1.5
                text: "O Plasma 6.5 chega com melhorias no gerenciamento de janelas, um novo painel de configurações rápidas e suporte aprimorado a HDR. A comunidade também dedicou este ciclo a corrigir centenas de pequenos problemas relatados pelos usuários."
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                font.family: "Noto Serif"; font.pixelSize: 18; lineHeight: 1.5
                text: "Entre as novidades mais pedidas está o modo de mosaico automático, que organiza as janelas sem esforço, e a nova tela de boas-vindas."
            }
        }

        // Controles flutuantes do modo leitura (QML, fora do HTML)
        Pane {
            anchors { right: parent.right; top: parent.top; margins: Kirigami.Units.largeSpacing }
            padding: Kirigami.Units.smallSpacing
            background: Rectangle {
                color: Kirigami.Theme.backgroundColor; radius: Kirigami.Units.cornerRadius
                border.color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.2)
            }
            RowLayout {
                spacing: 2
                ToolButton { icon.name: "format-font-size-less"; display: AbstractButton.IconOnly }
                Label { text: "18 px" }
                ToolButton { icon.name: "format-font-size-more"; display: AbstractButton.IconOnly }
                ToolButton { text: "Serifa"; icon.name: "format-text-symbol"; checkable: true; checked: true }
                ToolButton { text: "Sair"; icon.name: "window-close" }
            }
        }
    }
}
