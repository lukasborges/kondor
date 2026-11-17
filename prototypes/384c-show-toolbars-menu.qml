// #384 Main menu: "Show Toolbars" (Ctrl+Shift+F), checked by default, under the zoom row.
import QtQuick
import "common"

BrowserFrame {
    height: 720
    FakePage {}
    MainMenuMock { withShowToolbars: true }
}
