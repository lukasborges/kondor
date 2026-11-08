// Menu principal-alvo com as entradas de todas as issues (#1 #2 #3 #4 #5 #6 #14 #16 #17).
// Ordem e agrupamento seguem o padrão dos apps KDE (Arquivo / Editar / Exibir / Ferramentas).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    height: 760
    FakePage {}

    Menu {
        id: mainMenu
        popupType: Popup.Item
        x: frame.width - width - 8
        y: 0
        MenuItem { text: "Nova aba"; icon.name: "tab-new"; action: Action { shortcut: "Ctrl+T" } }
        MenuItem { text: "Nova janela"; icon.name: "window-new"; action: Action { shortcut: "Ctrl+N" } }
        MenuItem { text: "Nova janela privada"; icon.name: "view-private"; action: Action { shortcut: "Ctrl+Shift+P" } }
        MenuItem { text: "Reabrir aba fechada"; icon.name: "edit-undo"; action: Action { shortcut: "Ctrl+Shift+T" } }
        MenuSeparator {}
        Menu {
            title: "Favoritos"
            icon.name: "bookmarks"
            popupType: Popup.Item
            MenuItem { text: "Adicionar esta página"; icon.name: "bookmark-new" }
        }
        MenuItem { text: "Histórico"; icon.name: "view-history"; action: Action { shortcut: "Ctrl+H" } }
        MenuItem { text: "Downloads"; icon.name: "download"; action: Action { shortcut: "Ctrl+Shift+Y" } }
        MenuSeparator {}
        MenuItem { text: "Localizar na página…"; icon.name: "edit-find"; action: Action { shortcut: "Ctrl+F" } }
        MenuItem { text: "Salvar página como…"; icon.name: "document-save-as"; action: Action { shortcut: "Ctrl+S" } }
        MenuItem { text: "Salvar como PDF…"; icon.name: "document-export" }
        MenuItem { text: "Imprimir…"; icon.name: "document-print"; action: Action { shortcut: "Ctrl+P" } }
        MenuSeparator {}
        // Zoom numa linha só, como no Firefox/Falkon.
        MenuItem {
            id: zoomRow
            enabled: false
            contentItem: RowLayout {
                spacing: 0
                Label { text: "Zoom"; Layout.fillWidth: true; leftPadding: 30 }
                ToolButton { icon.name: "zoom-out"; display: AbstractButton.IconOnly }
                Label { text: "100%"; horizontalAlignment: Text.AlignHCenter; Layout.preferredWidth: 46 }
                ToolButton { icon.name: "zoom-in"; display: AbstractButton.IconOnly }
                ToolButton { icon.name: "view-fullscreen"; display: AbstractButton.IconOnly }
            }
        }
        MenuSeparator {}
        Menu {
            title: "Mais ferramentas"
            icon.name: "applications-utilities"
            popupType: Popup.Item
            MenuItem { text: "Ferramentas do desenvolvedor"; icon.name: "code-context" }
        }
        MenuItem { text: "Configurar o Kondor…"; icon.name: "configure"; action: Action { shortcut: "Ctrl+," } }
        MenuItem { text: "Sobre o Kondor"; icon.name: "help-about" }
        MenuSeparator {}
        MenuItem { text: "Sair"; icon.name: "application-exit"; action: Action { shortcut: "Ctrl+Q" } }
        Component.onCompleted: open()
    }
}
