// #349 Multiple profiles — the profile button before the main menu button: icon and
// name of the window's profile; a click opens the same Profiles menu as the main menu.
import QtQuick
import QtQuick.Controls
import "common"

BrowserFrame {
    height: 360
    toolbarExtras: [
        ToolButton {
            text: "Work"
            icon.name: "view-pim-tasks"
            display: AbstractButton.TextBesideIcon
            ToolTip.text: "Profile: Work"
            ToolTip.delay: 600
        }
    ]
    FakePage {}
}
