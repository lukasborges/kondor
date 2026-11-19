// #441 Translate pages on the device: the first time a language pair is used, its language files are downloaded once (progress in the panel; Cancel stops it); later translations work offline.
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
        state: "downloading"
        menuOpen: false
    }
}
