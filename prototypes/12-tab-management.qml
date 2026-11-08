// #12 Tab management — favicons, carregando, abas fixadas, aba privada e menu de contexto da aba.
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    tabs: [
        { title: "Correio", icon: "mail-message", pinned: true },
        { title: "Agenda", icon: "view-calendar", pinned: true },
        { title: "KDE Community", icon: "kde" },
        { title: "Carregando…", icon: "text-html", loading: true },
        { title: "Navegação privada", private: true },
        { title: "Qt Documentation", icon: "qtcreator" }
    ]
    currentTab: 2
    FakePage {}

    Menu {
        popupType: Popup.Item
        x: 300
        y: -50
        MenuItem { text: "Nova aba"; icon.name: "tab-new" }
        MenuSeparator {}
        MenuItem { text: "Recarregar"; icon.name: "view-refresh" }
        MenuItem { text: "Duplicar aba"; icon.name: "tab-duplicate" }
        MenuItem { text: "Fixar aba"; icon.name: "window-pin" }
        MenuItem { text: "Mover para nova janela"; icon.name: "window-new" }
        MenuSeparator {}
        MenuItem { text: "Fechar aba"; icon.name: "tab-close" }
        MenuItem { text: "Fechar outras abas"; icon.name: "tab-close-other" }
        MenuItem { text: "Fechar abas à direita"; icon.name: "go-last" }
        MenuSeparator {}
        MenuItem { text: "Reabrir aba fechada"; icon.name: "edit-undo" }
        Component.onCompleted: open()
    }
}
