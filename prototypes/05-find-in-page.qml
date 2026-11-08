// #5 Find in page — barra de busca (InlineBar) entre o cabeçalho e a página.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    address: "https://pt.wikipedia.org/wiki/KDE"
    tabs: [{ title: "KDE – Wikipédia, a enciclopédia livre", icon: "internet-web-browser" }]

    belowHeader: [
        // InlineBar: faixa com cores de View e separadores finos.
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: findRow.implicitHeight + 2 * Kirigami.Units.smallSpacing
            Kirigami.Theme.colorSet: Kirigami.Theme.View
            Kirigami.Theme.inherit: false
            color: Kirigami.Theme.backgroundColor
            Kirigami.Separator { anchors { left: parent.left; right: parent.right; top: parent.top } }
            Kirigami.Separator { anchors { left: parent.left; right: parent.right; bottom: parent.bottom } }

            RowLayout {
                id: findRow
                anchors { fill: parent; leftMargin: Kirigami.Units.largeSpacing; rightMargin: Kirigami.Units.smallSpacing }
                spacing: Kirigami.Units.smallSpacing

                Kirigami.Icon { source: "edit-find"; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
                TextField {
                    Layout.preferredWidth: 280
                    text: "Plasma"
                    placeholderText: "Localizar na página"
                    focus: true
                }
                ToolButton { icon.name: "go-up"; display: AbstractButton.IconOnly; ToolTip.text: "Anterior (Shift+F3)" }
                ToolButton { icon.name: "go-down"; display: AbstractButton.IconOnly; ToolTip.text: "Próximo (F3)" }
                Label { text: "3 de 12"; color: Kirigami.Theme.disabledTextColor; Layout.leftMargin: 6 }
                CheckBox { text: "Diferenciar maiúsculas"; Layout.leftMargin: 12 }
                Item { Layout.fillWidth: true }
                ToolButton { icon.name: "window-close"; display: AbstractButton.IconOnly; ToolTip.text: "Fechar (Esc)" }
            }
        }
    ]

    FakePage {
        heading: "KDE <mark>Plasma</mark>"
        paragraphs: [
            "O <mark>Plasma</mark> é o ambiente de trabalho desenvolvido pela comunidade KDE. Ele é leve, rápido e totalmente configurável, do painel aos atalhos de teclado.",
            "Com o <cur>Plasma</cur> 6, toda a pilha foi portada para o Qt 6 e para o KDE Frameworks 6, trazendo Wayland como sessão padrão, HDR e melhorias de acessibilidade."
        ]
    }
}
