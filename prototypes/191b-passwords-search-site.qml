// #191 The panel on open: the search field has the focus, and this site's accounts are listed as in #176.
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    height: 640
    address: "https://accounts.example.org/signin/identifier"
    tabs: [{ title: "Sign in · Example Accounts", icon: "internet-web-browser" }]
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    addressRight: [
        ToolButton { icon.name: "dialog-password"; display: AbstractButton.IconOnly; flat: true; checked: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    SignInPageMock {}

    SavedPasswordsPanelMock {
        x: 680
        y: -4
        level: "site"
        siteAccounts: ["user.one@example.org", "user.two@example.org", "u.one@example.org"]
    }
}
