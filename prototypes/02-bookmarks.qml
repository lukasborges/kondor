// #2 Bookmarks — estrela na barra de endereço, popup de edição (Ctrl+D) e barra de favoritos.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    addressRight: [
        ToolButton {
            icon.name: "rating"             // já favoritado (vazio: "rating-unrated")
            icon.width: 16; icon.height: 16
            display: AbstractButton.IconOnly
            flat: true
            implicitWidth: 28; implicitHeight: 28
        }
    ]
    belowHeader: [
        // Barra de favoritos (Ctrl+Shift+B)
        ToolBar {
            Layout.fillWidth: true
            Kirigami.Theme.colorSet: Kirigami.Theme.Window
            Kirigami.Theme.inherit: false
            position: ToolBar.Header
            RowLayout {
                spacing: 2
                Repeater {
                    model: [
                        { t: "KDE", i: "kde" }, { t: "Planet KDE", i: "internet-web-browser" },
                        { t: "Qt Docs", i: "internet-web-browser" }, { t: "Notícias", i: "folder" },
                        { t: "Desenvolvimento", i: "folder" }
                    ]
                    ToolButton {
                        text: modelData.t
                        icon.name: modelData.i
                        icon.width: 16; icon.height: 16
                        display: AbstractButton.TextBesideIcon
                        flat: true
                    }
                }
            }
        }
    ]
    FakePage {}

    Popup {
        popupType: Popup.Item
        x: frame.width - width - 50
        y: -4
        width: 330
        padding: Kirigami.Units.largeSpacing
        Component.onCompleted: open()
        contentItem: ColumnLayout {
            spacing: Kirigami.Units.largeSpacing
            Kirigami.Heading { level: 4; text: "Página adicionada aos favoritos" }
            Kirigami.FormLayout {
                Layout.fillWidth: true
                TextField { Kirigami.FormData.label: "Nome:"; text: "KDE Community"; Layout.fillWidth: true }
                ComboBox { Kirigami.FormData.label: "Pasta:"; model: ["Barra de favoritos", "Outros favoritos", "Notícias"]; Layout.fillWidth: true }
            }
            RowLayout {
                Layout.fillWidth: true
                Button { text: "Remover"; icon.name: "edit-delete" }
                Item { Layout.fillWidth: true }
                Button { text: "Concluído"; icon.name: "dialog-ok-apply"; highlighted: true }
            }
        }
    }
}
