// #13 Page context menu — clique direito sobre um link (com texto selecionado na página).
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    FakePage {
        paragraphs: [
            "O Plasma é o ambiente de trabalho desenvolvido pela comunidade KDE. Saiba mais na <a href='#'>página de recursos do Plasma</a>.",
            "Com o Plasma 6, toda a pilha foi portada para o Qt 6 e para o KDE Frameworks 6, trazendo Wayland como sessão padrão, HDR e melhorias de acessibilidade."
        ]
    }

    Menu {
        popupType: Popup.Item
        x: 330
        y: 150
        MenuItem { text: "Abrir link em nova aba"; icon.name: "tab-new" }
        MenuItem { text: "Abrir link em nova aba privada"; icon.name: "view-private" }
        MenuItem { text: "Abrir link em nova janela"; icon.name: "window-new" }
        MenuSeparator {}
        MenuItem { text: "Copiar endereço do link"; icon.name: "edit-copy" }
        MenuItem { text: "Salvar link como…"; icon.name: "document-save" }
        MenuSeparator {}
        MenuItem { text: "Copiar"; icon.name: "edit-copy" }
        MenuItem { text: "Pesquisar «recursos do Plasma» no DuckDuckGo"; icon.name: "edit-find" }
        MenuSeparator {}
        MenuItem { text: "Inspecionar elemento"; icon.name: "code-context" }
        Component.onCompleted: open()
    }
}
