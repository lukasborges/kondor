// #24 Per-site zoom — "125%" indicator in the address bar (click resets to 100%).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    addressRight: [
        ToolButton {
            text: "125%"
            icon.name: "zoom-in"
            icon.width: 16; icon.height: 16
            display: AbstractButton.TextBesideIcon
            flat: true
            implicitHeight: 28
            ToolTip.text: "Reset Zoom (Ctrl+0)"
        }
    ]
    Item {
        anchors.fill: parent
        FakePage { anchors.fill: undefined; width: parent.width / 1.25; height: parent.height / 1.25; scale: 1.25; transformOrigin: Item.TopLeft }
    }
}
