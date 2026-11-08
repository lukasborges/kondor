// #3 Settings — janela "Configurar o Kondor" (Ctrl+,): páginas à esquerda, Kirigami.FormLayout à direita.
// Mudanças aplicam na hora (sem OK/Aplicar), como nos apps KDE.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    width: 820
    height: 560
    color: Kirigami.Theme.backgroundColor

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Lista de páginas (como o KConfigDialog / System Settings)
        ScrollView {
            Layout.preferredWidth: 200
            Layout.fillHeight: true
            Kirigami.Theme.colorSet: Kirigami.Theme.View
            Kirigami.Theme.inherit: false
            background: Rectangle { color: Kirigami.Theme.backgroundColor }
            ListView {
                model: [
                    { t: "Geral", i: "go-home" }, { t: "Pesquisa", i: "edit-find" }, { t: "Downloads", i: "download" },
                    { t: "Privacidade", i: "security-high" }, { t: "Senhas", i: "dialog-password" },
                    { t: "Ortografia", i: "tools-check-spelling" }
                ]
                delegate: ItemDelegate {
                    required property var modelData
                    required property int index
                    width: ListView.view.width
                    highlighted: index === 0
                    icon.name: modelData.i
                    text: modelData.t
                }
            }
        }
        Kirigami.Separator { Layout.fillHeight: true }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: Kirigami.Units.largeSpacing * 2
            spacing: Kirigami.Units.largeSpacing

            Kirigami.FormLayout {
                Layout.fillWidth: true

                Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: "Ao iniciar" }
                RadioButton { Kirigami.FormData.label: "Abrir:"; text: "A página inicial"; checked: true }
                RadioButton { text: "As abas da sessão anterior" }

                Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: "Página inicial" }
                RowLayout {
                    Kirigami.FormData.label: "Endereço:"
                    TextField { text: "https://duckduckgo.com"; Layout.preferredWidth: 280 }
                    Button { text: "Usar página atual"; icon.name: "go-home" }
                }

                Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: "Pesquisa" }
                ComboBox { Kirigami.FormData.label: "Mecanismo:"; model: ["DuckDuckGo", "Google", "Startpage", "Brave Search", "Personalizado…"]; Layout.preferredWidth: 280 }
                CheckBox { Kirigami.FormData.label: "Sugestões:"; text: "Mostrar sugestões do mecanismo de pesquisa" }

                Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: "Aparência" }
                CheckBox { Kirigami.FormData.label: "Barras:"; text: "Mostrar barra de favoritos"; checked: true }
            }
            Item { Layout.fillHeight: true }
        }
    }
}
