// #93 Main menu — More Tools submenu.
import QtQuick
import "common"

BrowserFrame {
    height: 720
    FakePage {}
    MainMenuMock { openSubmenu: "tools" }
}
