// #384 Toolbars hidden ("Show Toolbars" off, or F11 full screen): only the page, under the window
// decoration (not drawn here). Nothing is left at the top edge.
import QtQuick
import "common"

BrowserFrame {
    showHeader: false
    FakePage {}
}
