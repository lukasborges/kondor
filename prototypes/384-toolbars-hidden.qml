// #384 Toolbars hidden ("Hide Toolbars" on, or F11 full screen): only the page, under the window
// decoration (not drawn here). Nothing is left at the top edge.
import QtQuick
import "common"

BrowserFrame {
    showHeader: false
    FakePage {}
}
