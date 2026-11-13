// #107 Kondor extensions — the toolbar Extensions menu on a YouTube tab.
import QtQuick
import QtQuick.Controls
import "common"

BrowserFrame {
    height: 620
    address: "https://www.youtube.com/watch?v=example"
    toolbarExtras: ToolButton { display: AbstractButton.IconOnly; icon.name: "plugins"; checked: true }
    FakePage {}
    ExtensionsMenuMock {}
}
