// #2 Bookmarks — janela "Gerenciar favoritos" (Ctrl+Shift+O): pastas à esquerda, itens à direita.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    width: 820
    height: 540
    color: Kirigami.Theme.backgroundColor

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        ToolBar {
            Layout.fillWidth: true
            RowLayout {
                anchors.fill: parent
                ToolButton { text: "Nova pasta"; icon.name: "folder-new" }
                ToolButton { text: "Renomear"; icon.name: "edit-rename" }
                ToolButton { text: "Excluir"; icon.name: "edit-delete" }
                ToolButton { icon.name: "go-up"; display: AbstractButton.IconOnly }
                ToolButton { icon.name: "go-down"; display: AbstractButton.IconOnly }
                Item { Layout.fillWidth: true }
                ToolButton { text: "Importar de HTML…"; icon.name: "document-import" }
                TextField { placeholderText: "Pesquisar favoritos…"; Layout.preferredWidth: 200 }
            }
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ScrollView {
                SplitView.preferredWidth: 240
                Kirigami.Theme.colorSet: Kirigami.Theme.View
                background: Rectangle { color: Kirigami.Theme.backgroundColor }
                ListView {
                    currentIndex: 0
                    model: [
                        { t: "Barra de favoritos", d: 0 }, { t: "Notícias", d: 1 }, { t: "Desenvolvimento", d: 1 },
                        { t: "Outros favoritos", d: 0 }, { t: "Importados", d: 0 }, { t: "Firefox", d: 1 }
                    ]
                    delegate: ItemDelegate {
                        required property var modelData
                        required property int index
                        width: ListView.view.width
                        highlighted: index === 0
                        icon.name: "folder"
                        text: modelData.t
                        leftPadding: 10 + modelData.d * 18
                    }
                }
            }

            ScrollView {
                Kirigami.Theme.colorSet: Kirigami.Theme.View
                background: Rectangle { color: Kirigami.Theme.backgroundColor }
                ListView {
                    model: [
                        { t: "Notícias", u: "", f: true }, { t: "Desenvolvimento", u: "", f: true },
                        { t: "KDE", u: "https://kde.org/" }, { t: "Planet KDE", u: "https://planet.kde.org/" },
                        { t: "Qt Docs", u: "https://doc.qt.io/qt-6/" }, { t: "KDE Human Interface Guidelines", u: "https://develop.kde.org/hig/" }
                    ]
                    delegate: ItemDelegate {
                        required property var modelData
                        required property int index
                        width: ListView.view.width
                        highlighted: index === 3
                        contentItem: RowLayout {
                            spacing: Kirigami.Units.largeSpacing
                            Kirigami.Icon { source: modelData.f ? "folder" : "internet-web-browser"; Layout.preferredWidth: 22; Layout.preferredHeight: 22 }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 0
                                Label { text: modelData.t; font.bold: true; Layout.fillWidth: true }
                                Label { visible: !modelData.f; text: modelData.u; color: Kirigami.Theme.disabledTextColor; font: Kirigami.Theme.smallFont }
                            }
                        }
                    }
                }
            }
        }
    }
}
