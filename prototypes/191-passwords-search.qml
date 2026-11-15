// #191 Searching every saved password: this site's logins first, then the other sites, sorted by site.
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
        level: "search"
        query: "example"
        results: [
            { host: "accounts.example.org", username: "user.one@example.org", icon: "internet-web-browser" },
            { host: "accounts.example.org", username: "user.two@example.org", icon: "internet-web-browser" },
            { host: "example.com", username: "user.one", icon: "globe" },
            { host: "forum.example.net", username: "user_one", icon: "globe" },
            { host: "id.example.org", username: "user.one@example.org", icon: "internet-web-browser" },
            { host: "mail.example.org", username: "user.one@example.org", icon: "mail-message" },
            { host: "shop.example.com", username: "user.one@example.org", icon: "globe" },
            { host: "status.example.org", username: "admin", icon: "globe" },
            { host: "www.example.org", username: "user.one@example.org", icon: "internet-web-browser" },
            { host: "wiki.example.org", username: "user.two", icon: "globe" },
            { host: "git.example.dev", username: "user-one", icon: "globe" }
        ]
    }
}
