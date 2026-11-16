// #349 Multiple profiles — main menu → Profiles (each row opens a window of that profile) and the
// profile button in the toolbar, shown only when more than one profile exists.
import QtQuick
import QtQuick.Controls
import "common"

BrowserFrame {
    height: 720
    toolbarExtras: [
        ToolButton {
            text: "Personal"
            icon.name: "im-user"
            display: AbstractButton.TextBesideIcon
            ToolTip.text: "Profile: Personal"
            ToolTip.delay: 600
        }
    ]
    FakePage {}
    MainMenuMock { withProfiles: true; openSubmenu: "profiles" }
}
