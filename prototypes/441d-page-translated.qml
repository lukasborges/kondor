// #441 Translate pages on the device: the page is shown translated; the button stays checked and the panel offers Show Original. Changing To translates again.
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    height: 560
    address: "https://kde.org/"
    tabs: [{ title: "Plasma 6: o desktop da comunidade KDE", icon: "kde" }]
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    addressRight: [
        ToolButton { icon.name: "translate"; icon.width: 16; icon.height: 16; display: AbstractButton.IconOnly; flat: true; checked: true; implicitWidth: 28; implicitHeight: 28 },
        ToolButton { icon.name: "non-starred-symbolic"; icon.width: 16; icon.height: 16; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    FakePage {
        heading: "Plasma 6: o desktop da comunidade KDE"
        paragraphs: ["O Plasma é o ambiente de trabalho feito pela comunidade KDE. Ele é leve, rápido e totalmente configurável, dos painéis aos atalhos de teclado.", "Com o Plasma 6, toda a pilha passou para o Qt 6 e o KDE Frameworks 6, trazendo o Wayland como sessão padrão, HDR e melhorias de acessibilidade."]
        paragraphsAfter: ["Aplicativos como Dolphin, Konsole, Kate e Okular seguem as mesmas Diretrizes de Interface Humana e o tema Breeze, para uma experiência consistente."]
    }

    TranslatePopupMock {
        x: frame.width - width - 96
        y: -4
        state: "translated"
        menuOpen: false
    }
}
