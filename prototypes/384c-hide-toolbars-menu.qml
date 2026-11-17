// #384 Main menu: "Hide Toolbars" (Ctrl+Shift+F), unchecked by default, under the zoom row.
import QtQuick
import "common"

BrowserFrame {
    height: 720
    FakePage {}
    MainMenuMock { withHideToolbars: true }
}
