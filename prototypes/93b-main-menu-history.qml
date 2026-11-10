// #93 Main menu — History submenu (recently closed tabs, today's history).
import QtQuick
import "common"

BrowserFrame {
    height: 720
    FakePage {}
    MainMenuMock { openSubmenu: "history" }
}
