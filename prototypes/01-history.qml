// #1 Browsing history — janela "Histórico" (Ctrl+H): busca, grupos por dia, menu de contexto.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    id: root
    width: 760
    height: 600
    color: Kirigami.Theme.backgroundColor

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        ToolBar {
            Layout.fillWidth: true
            RowLayout {
                anchors.fill: parent
                Kirigami.SearchField { Layout.fillWidth: true; placeholderText: "Pesquisar no histórico…" }
                ToolButton { text: "Limpar histórico…"; icon.name: "edit-clear-history" }
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Kirigami.Theme.colorSet: Kirigami.Theme.View
            Kirigami.Theme.inherit: false
            background: Rectangle { color: Kirigami.Theme.backgroundColor }
            ListView {
                id: list
                clip: true
                section.property: "day"
                section.delegate: Kirigami.ListSectionHeader { required property string section; width: ListView.view.width; text: section }
                model: ListModel {
                    ListElement { day: "Hoje"; time: "14:32"; title: "KDE Community"; url: "https://kde.org/" }
                    ListElement { day: "Hoje"; time: "14:10"; title: "Plasma 6.5 — Notas da versão"; url: "https://kde.org/announcements/plasma/6/6.5.0/" }
                    ListElement { day: "Hoje"; time: "11:47"; title: "KDE – Wikipédia, a enciclopédia livre"; url: "https://pt.wikipedia.org/wiki/KDE" }
                    ListElement { day: "Ontem"; time: "21:05"; title: "Qt WebEngine Overview | Qt 6"; url: "https://doc.qt.io/qt-6/qtwebengine-overview.html" }
                    ListElement { day: "Ontem"; time: "20:58"; title: "Kirigami — KDE Developer"; url: "https://develop.kde.org/frameworks/kirigami/" }
                    ListElement { day: "Ontem"; time: "09:12"; title: "Planet KDE"; url: "https://planet.kde.org/" }
                    ListElement { day: "terça-feira, 4 de novembro de 2026"; time: "18:20"; title: "KDE Human Interface Guidelines"; url: "https://develop.kde.org/hig/" }
                }
                delegate: ItemDelegate {
                    required property string time
                    required property string title
                    required property string url
                    required property int index
                    width: ListView.view.width
                    highlighted: index === 1
                    contentItem: RowLayout {
                        spacing: Kirigami.Units.largeSpacing
                        Label { text: time; color: Kirigami.Theme.disabledTextColor; Layout.preferredWidth: 44 }
                        Kirigami.Icon { source: "internet-web-browser"; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
                        Label { text: title; elide: Text.ElideRight; Layout.maximumWidth: 330 }
                        Label { text: url; elide: Text.ElideRight; color: highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.disabledTextColor; Layout.fillWidth: true }
                    }
                }
            }
        }
    }

    Menu {
        popupType: Popup.Item
        x: 300
        y: 150
        MenuItem { text: "Abrir"; icon.name: "go-jump" }
        MenuItem { text: "Abrir em nova aba"; icon.name: "tab-new" }
        MenuItem { text: "Abrir em nova aba privada"; icon.name: "view-private" }
        MenuSeparator {}
        MenuItem { text: "Copiar endereço"; icon.name: "edit-copy" }
        MenuItem { text: "Adicionar aos favoritos"; icon.name: "bookmark-new" }
        MenuSeparator {}
        MenuItem { text: "Remover do histórico"; icon.name: "edit-delete" }
        Component.onCompleted: open()
    }
}
