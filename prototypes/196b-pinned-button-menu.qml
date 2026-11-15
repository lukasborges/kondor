// #196 Right-click on a pinned extension button: Unpin from Toolbar.
import QtQuick
import QtQuick.Controls
import "common"

BrowserFrame {
    id: frame
    height: 330
    address: "https://www.youtube.com/watch?v=example"
    toolbarExtras: [
        ToolButton { display: AbstractButton.IconOnly; icon.name: "media-playback-start"; down: true },
        ToolButton { display: AbstractButton.IconOnly; icon.name: "plugins" }
    ]
    FakePage {}
    Menu {
        popupType: Popup.Item
        x: frame.width - width - 60
        y: -4
        Component.onCompleted: open()
        MenuItem { text: "Unpin from Toolbar"; icon.name: "window-unpin" }
    }
}
