// #441 Translate pages on the device: the panel's More Options menu: always or never translate a language, never translate this site, manage the downloaded languages.
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    height: 560
    address: "https://kde.org/"
    tabs: [{ title: "Plasma 6: the KDE community desktop", icon: "kde" }]
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    addressRight: [
        ToolButton { icon.name: "translate"; icon.width: 16; icon.height: 16; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 },
        ToolButton { icon.name: "non-starred-symbolic"; icon.width: 16; icon.height: 16; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    FakePage {}

    TranslatePopupMock {
        x: frame.width - width - 96
        y: -4
        state: "offer"
        menuOpen: true
    }
}
