// #191 A site with no saved password: the key button is there anyway, so the search still works.
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
        level: "empty"
    }
}
