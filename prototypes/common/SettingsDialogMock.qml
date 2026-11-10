// Shared mock for the "Configure — Kondor Browser" window (#3, reworked by #57),
// modelled on KDE's KConfigDialog (e.g. Configure — Dolphin): a sidebar with a
// search field and big icons, the page title on top, optional tabs inside a
// page, and Defaults / OK / Apply / Cancel at the bottom.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    id: root
    property int page: 0          // 0 General, 1 Search, 2 Downloads, 3 Privacy, 4 Passwords (#21)
    property int innerTab: 0      // tabs of the General and Passwords pages
    property bool withPasswords: false // show the Passwords page added by #21
    property bool walletDenied: false  // #21: KWallet disabled / access denied
    property string search: ""
    property bool modified: false // pending changes → Apply enabled

    width: 860
    height: 600
    color: Kirigami.Theme.backgroundColor

    readonly property var pages: [
        { title: "General", icon: "internet-web-browser" },
        { title: "Search", icon: "system-search" },
        { title: "Downloads", icon: "folder-download" },
        { title: "Privacy", icon: "preferences-security" },
        { title: "Passwords", icon: "preferences-desktop-user-password" }
    ]

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // ── Sidebar ──────────────────────────────────────────────────
            Rectangle {
                Layout.preferredWidth: Kirigami.Units.gridUnit * 8
                Layout.fillHeight: true
                Kirigami.Theme.colorSet: Kirigami.Theme.View
                Kirigami.Theme.inherit: false
                color: Kirigami.Theme.backgroundColor

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Kirigami.Units.smallSpacing
                    spacing: Kirigami.Units.smallSpacing

                    // Kirigami.SearchField in the app (Ctrl+F focuses it). The
                    // mock uses a TextField because the offscreen render shows
                    // SearchField's shortcut hint over the first page.
                    TextField {
                        Layout.fillWidth: true
                        text: root.search
                        placeholderText: "Search…"
                        leftPadding: Kirigami.Units.iconSizes.small + Kirigami.Units.largeSpacing
                        Kirigami.Icon {
                            source: "search"
                            width: Kirigami.Units.iconSizes.small
                            height: width
                            anchors.left: parent.left
                            anchors.leftMargin: Kirigami.Units.smallSpacing
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }

                    Repeater {
                        model: root.withPasswords ? root.pages : root.pages.slice(0, 4)
                        delegate: ItemDelegate {
                            required property var modelData
                            required property int index
                            Layout.fillWidth: true
                            visible: root.search === "" || index === root.page
                            highlighted: index === root.page
                            focus: index === root.page
                            display: AbstractButton.TextUnderIcon
                            icon.name: modelData.icon
                            icon.width: Kirigami.Units.iconSizes.medium
                            icon.height: Kirigami.Units.iconSizes.medium
                            text: modelData.title
                        }
                    }
                    Item { Layout.fillHeight: true }
                }
            }
            Kirigami.Separator { Layout.fillHeight: true }

            // ── Page ─────────────────────────────────────────────────────
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 0

                Kirigami.Heading {
                    Layout.fillWidth: true
                    Layout.margins: Kirigami.Units.smallSpacing
                    Layout.leftMargin: Kirigami.Units.largeSpacing
                    level: 1
                    text: root.pages[root.page].title
                }

                TabBar {
                    id: bar
                    Layout.fillWidth: true
                    visible: root.page === 0 || root.page === 4
                    currentIndex: root.innerTab
                    TabButton { text: root.page === 4 ? "Saved Passwords" : "Startup" }
                    TabButton { text: root.page === 4 ? "Never Saved" : "New Tabs" }
                }
                Kirigami.Separator { Layout.fillWidth: true; visible: root.page !== 0 && root.page !== 4 }

                StackLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.margins: Kirigami.Units.gridUnit
                    currentIndex: root.page === 0 ? root.innerTab
                                : root.page === 4 ? 5 + root.innerTab
                                : root.page + 1

                    // General → Startup
                    Kirigami.FormLayout {
                        RadioButton { Kirigami.FormData.label: "On startup:"; text: "Open the home page"; checked: true }
                        RadioButton { text: "Open the tabs from last time" }
                        Item { Kirigami.FormData.isSection: true }
                        TextField {
                            Kirigami.FormData.label: "Home page:"
                            placeholderText: "New Tab page"
                            text: "https://kde.org"
                            Layout.preferredWidth: Kirigami.Units.gridUnit * 18
                        }
                        RowLayout {
                            Button { text: "Use Current Page"; icon.name: "go-home" }
                            Button { text: "Use New Tab Page"; icon.name: "tab-new" }
                        }
                    }

                    // General → New Tabs
                    Kirigami.FormLayout {
                        CheckBox { Kirigami.FormData.label: "New Tab page:"; text: "Show top sites"; checked: true }
                        Button { text: "Restore Removed Sites"; icon.name: "edit-undo" }
                    }

                    // Search
                    Kirigami.FormLayout {
                        ComboBox {
                            Kirigami.FormData.label: "Search engine:"
                            model: ["DuckDuckGo", "Google", "Startpage", "Brave Search", "Custom"]
                            Layout.preferredWidth: Kirigami.Units.gridUnit * 14
                        }
                        TextField {
                            Kirigami.FormData.label: "Custom URL:"
                            enabled: false
                            placeholderText: "https://example.com/search?q=%1"
                            Layout.preferredWidth: Kirigami.Units.gridUnit * 18
                        }
                    }

                    // Downloads
                    Kirigami.FormLayout {
                        RowLayout {
                            Kirigami.FormData.label: "Save files to:"
                            TextField { text: "/home/user/Downloads"; readOnly: true; Layout.preferredWidth: Kirigami.Units.gridUnit * 16 }
                            Button { text: "Choose…"; icon.name: "document-open-folder" }
                        }
                        CheckBox { text: "Ask where to save each file" }
                    }

                    // Privacy
                    Kirigami.FormLayout {
                        CheckBox { Kirigami.FormData.label: "Cookies:"; text: "Block third-party cookies"; checked: true }
                        CheckBox { Kirigami.FormData.label: "On exit:"; text: "Clear cookies, cache and history" }
                        Item { Kirigami.FormData.isSection: true }
                        Button { Kirigami.FormData.label: "Browsing data:"; text: "Clear Cookies and Cache Now"; icon.name: "edit-clear-history" }
                    }

                    // Passwords → Saved Passwords (#21)
                    ColumnLayout {
                        spacing: Kirigami.Units.largeSpacing

                        Kirigami.InlineMessage {
                            Layout.fillWidth: true
                            visible: root.walletDenied
                            type: Kirigami.MessageType.Warning
                            text: "KWallet is disabled or access to it was denied, so passwords cannot be saved or filled."
                            actions: [ Kirigami.Action { text: "Try Again"; icon.name: "view-refresh" } ]
                        }
                        CheckBox { text: "Offer to save passwords"; checked: true; enabled: !root.walletDenied }
                        TextField {
                            Layout.fillWidth: true
                            enabled: !root.walletDenied
                            placeholderText: "Filter by site or username…"
                        }
                        Frame {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            padding: 0
                            enabled: !root.walletDenied
                            Kirigami.Theme.colorSet: Kirigami.Theme.View
                            Kirigami.Theme.inherit: false
                            background: Rectangle {
                                color: Kirigami.Theme.backgroundColor
                                border.color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.2)
                            }
                            ListView {
                                anchors.fill: parent
                                clip: true
                                visible: !root.walletDenied
                                section.property: "site"
                                section.delegate: Kirigami.ListSectionHeader {
                                    required property string section
                                    width: ListView.view.width
                                    text: section
                                }
                                model: ListModel {
                                    ListElement { site: "invent.kde.org"; user: "maria"; shown: true }
                                    ListElement { site: "invent.kde.org"; user: "maria.dev"; shown: false }
                                    ListElement { site: "lwn.net"; user: "maria@example.org"; shown: false }
                                    ListElement { site: "store.kde.org"; user: "maria"; shown: false }
                                }
                                delegate: ItemDelegate {
                                    required property string user
                                    required property bool shown
                                    width: ListView.view.width
                                    contentItem: RowLayout {
                                        spacing: Kirigami.Units.largeSpacing
                                        Label { text: user; Layout.preferredWidth: Kirigami.Units.gridUnit * 10; elide: Text.ElideRight }
                                        Label {
                                            Layout.fillWidth: true
                                            text: shown ? "correct-horse-battery" : "••••••••••"
                                            font.family: shown ? "monospace" : Kirigami.Theme.defaultFont.family
                                        }
                                        ToolButton {
                                            icon.name: shown ? "view-hidden" : "view-visible"
                                            display: AbstractButton.IconOnly
                                            text: shown ? "Hide Password" : "Show Password"
                                        }
                                        ToolButton { icon.name: "edit-copy"; display: AbstractButton.IconOnly; text: "Copy Password" }
                                        ToolButton { icon.name: "edit-delete"; display: AbstractButton.IconOnly; text: "Delete" }
                                    }
                                }
                            }
                        }
                    }

                    // Passwords → Never Saved (#21)
                    ColumnLayout {
                        spacing: Kirigami.Units.largeSpacing
                        Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            text: "Kondor never offers to save passwords on these sites."
                        }
                        Frame {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            padding: 0
                            Kirigami.Theme.colorSet: Kirigami.Theme.View
                            Kirigami.Theme.inherit: false
                            background: Rectangle {
                                color: Kirigami.Theme.backgroundColor
                                border.color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.2)
                            }
                            ListView {
                                anchors.fill: parent
                                clip: true
                                model: ["accounts.example.com", "bank.example.net"]
                                delegate: ItemDelegate {
                                    required property string modelData
                                    width: ListView.view.width
                                    contentItem: RowLayout {
                                        Label { text: modelData; Layout.fillWidth: true }
                                        Button { text: "Remove"; icon.name: "list-remove"; flat: true }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // ── Buttons ──────────────────────────────────────────────────────
        Kirigami.Separator { Layout.fillWidth: true }
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            Button { text: "Defaults"; icon.name: "document-revert" }
            Item { Layout.fillWidth: true }
            Button { text: "OK"; icon.name: "dialog-ok"; highlighted: true }
            Button { text: "Apply"; icon.name: "dialog-ok-apply"; enabled: root.modified }
            Button { text: "Cancel"; icon.name: "dialog-cancel" }
        }
    }
}
