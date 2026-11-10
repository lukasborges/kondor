// #93 Main menu — Help submenu.
import QtQuick
import "common"

BrowserFrame {
    height: 720
    FakePage {}
    MainMenuMock { openSubmenu: "help" }
}
