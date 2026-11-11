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
    property bool passwordsEmpty: false // #102: no saved passwords (placeholder)
    property string passwordsFilter: "" // #102: text in the filter field
    property bool addPasswordDialog: false // #102: the "Add Password" dialog is open
    property bool addPasswordDuplicate: false // #102: the dialog's login is already saved
    property bool importDialog: false // #106: the "Import Passwords" review dialog is open
    property bool importUnrecognized: false // #106: the chosen file is not a password export
    property bool importDone: false // #106: an import just finished (message on the page)
    property bool withExtensions: false // #107: show the Extensions page
    property bool extensionsEmpty: false // #107: no extension installed (placeholder)
    property bool catalogDialog: false // #107: the "Get New Extensions" dialog is open
    property bool installDialog: false // #107: the install confirmation is open
    property bool installFromFile: false // #107: the confirmation is for a .kondorext file
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
        { title: "Passwords", icon: "preferences-desktop-user-password" },
        { title: "Extensions", icon: "preferences-plugin" }
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
                        model: root.withExtensions ? root.pages : root.withPasswords ? root.pages.slice(0, 5) : root.pages.slice(0, 4)
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
                                : root.page === 5 ? 7
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
                        Kirigami.InlineMessage {
                            Layout.fillWidth: true
                            visible: root.importDone
                            type: Kirigami.MessageType.Positive
                            showCloseButton: true
                            text: "Imported 38 passwords from “bitwarden_export.csv”. The file holds your passwords unencrypted: delete it when you no longer need it."
                            actions: [ Kirigami.Action { text: "Move File to Trash"; icon.name: "user-trash" } ]
                        }
                        CheckBox { text: "Offer to save passwords"; checked: true; enabled: !root.walletDenied }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Kirigami.Units.smallSpacing
                            TextField {
                                Layout.fillWidth: true
                                enabled: !root.walletDenied
                                placeholderText: "Filter by site or username…"
                                text: root.passwordsFilter
                            }
                            Button {
                                text: "Add Password…"
                                icon.name: "list-add"
                                enabled: !root.walletDenied
                            }
                            Button {
                                text: "Import…"
                                icon.name: "document-import"
                                enabled: !root.walletDenied
                            }
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
                            Kirigami.PlaceholderMessage {
                                anchors.centerIn: parent
                                width: parent.width - Kirigami.Units.gridUnit * 4
                                visible: !root.walletDenied && root.passwordsEmpty
                                icon.name: root.passwordsFilter.length ? "edit-none" : "dialog-password"
                                text: root.passwordsFilter.length
                                      ? "No saved passwords match “" + root.passwordsFilter + "”"
                                      : "No saved passwords"
                                explanation: root.passwordsFilter.length
                                             ? ""
                                             : "Kondor offers to save a password when you log in to a site. You can also add one here, or import the CSV file exported by another browser or password manager."
                                helpfulAction: root.passwordsFilter.length ? null : addAction
                                Kirigami.Action { id: addAction; text: "Add Password…"; icon.name: "list-add" }
                            }
                            ListView {
                                anchors.fill: parent
                                clip: true
                                visible: !root.walletDenied && !root.passwordsEmpty
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

                    // Extensions (#107)
                    ColumnLayout {
                        spacing: Kirigami.Units.largeSpacing
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Kirigami.Units.smallSpacing
                            TextField { Layout.fillWidth: true; placeholderText: "Filter extensions…" }
                            Button { text: "Get New Extensions…"; icon.name: "get-hot-new-stuff" }
                            Button { text: "Install from File…"; icon.name: "document-import" }
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
                            Kirigami.PlaceholderMessage {
                                anchors.centerIn: parent
                                width: parent.width - Kirigami.Units.gridUnit * 4
                                visible: root.extensionsEmpty
                                icon.name: "preferences-plugin"
                                text: "No extensions installed"
                                explanation: "Extensions add features to Kondor. Get them from the Kondor extensions catalog, or install a .kondorext file."
                                helpfulAction: Kirigami.Action { text: "Get New Extensions…"; icon.name: "get-hot-new-stuff" }
                            }
                            ListView {
                                anchors.fill: parent
                                clip: true
                                visible: !root.extensionsEmpty
                                model: ListModel {
                                    ListElement { iconName: "weather-clear-night"; name: "Dark Mode"; version: "1.0.0"; desc: "Shows every site with dark colors."; access: "Read and change all websites"; on: true; review: false }
                                    ListElement { iconName: "media-playback-start"; name: "Video Speed Controller"; version: "1.2.0"; desc: "Change the playback speed of any video with the keyboard."; access: "Read and change all websites"; on: true; review: true }
                                    ListElement { iconName: "application-json"; name: "JSON Viewer"; version: "0.9.1"; desc: "Formats JSON documents and lets you fold them."; access: "Read and change all websites"; on: false; review: false }
                                }
                                delegate: ItemDelegate {
                                    required property string iconName
                                    required property string name
                                    required property string version
                                    required property string desc
                                    required property string access
                                    required property bool on
                                    required property bool review
                                    width: ListView.view.width
                                    contentItem: RowLayout {
                                        spacing: Kirigami.Units.largeSpacing
                                        Kirigami.Icon { source: iconName; Layout.preferredWidth: Kirigami.Units.iconSizes.medium; Layout.preferredHeight: Layout.preferredWidth }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 0
                                            RowLayout {
                                                Label { text: name; font.bold: true }
                                                Label { text: version; opacity: 0.7; font: Kirigami.Theme.smallFont }
                                            }
                                            Label { Layout.fillWidth: true; text: desc; elide: Text.ElideRight }
                                            Label { Layout.fillWidth: true; text: access; opacity: 0.7; font: Kirigami.Theme.smallFont; elide: Text.ElideRight }
                                        }
                                        Button { visible: review; text: "Update…"; icon.name: "update-none" }
                                        Switch { checked: on }
                                        ToolButton { icon.name: "configure"; display: AbstractButton.IconOnly; text: "Configure…" }
                                        ToolButton { icon.name: "edit-delete"; display: AbstractButton.IconOnly; text: "Remove" }
                                    }
                                }
                            }
                        }
                        CheckBox { text: "Update extensions automatically"; checked: true }
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

    // ── Add Password dialog (#102) ──────────────────────────────────────
    Dialog {
        id: addDialog
        parent: root
        anchors.centerIn: parent
        width: Kirigami.Units.gridUnit * 24
        modal: true
        dim: true
        visible: root.addPasswordDialog
        title: "Add Password"
        standardButtons: Dialog.Save | Dialog.Cancel

        contentItem: ColumnLayout {
            spacing: Kirigami.Units.largeSpacing

            Kirigami.FormLayout {
                Layout.fillWidth: true
                TextField {
                    Kirigami.FormData.label: "Website:"
                    Layout.fillWidth: true
                    placeholderText: "https://example.com"
                    text: "https://invent.kde.org"
                }
                TextField {
                    Kirigami.FormData.label: "Username:"
                    Layout.fillWidth: true
                    text: root.addPasswordDuplicate ? "maria" : "maria.review"
                }
                Kirigami.PasswordField {
                    Kirigami.FormData.label: "Password:"
                    Layout.fillWidth: true
                    text: "correct-horse-battery"
                }
            }

            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: root.addPasswordDuplicate
                type: Kirigami.MessageType.Warning
                text: "A password for maria on invent.kde.org is already saved. Saving replaces it."
            }
        }
    }

    // ── Import Passwords dialog (#106) ──────────────────────────────────
    Dialog {
        id: importDialog
        parent: root
        anchors.centerIn: parent
        width: Kirigami.Units.gridUnit * 34
        modal: true
        dim: true
        visible: root.importDialog
        title: "Import Passwords"
        footer: DialogButtonBox {
            Button {
                visible: !root.importUnrecognized
                text: "Import 38 Passwords"
                icon.name: "document-import"
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Button {
                text: root.importUnrecognized ? "Close" : "Cancel"
                icon.name: root.importUnrecognized ? "dialog-close" : "dialog-cancel"
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }

        contentItem: ColumnLayout {
            spacing: Kirigami.Units.largeSpacing

            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: root.importUnrecognized
                type: Kirigami.MessageType.Error
                text: "“notes.csv” is not a password export: it has no website, username and password columns."
            }

            Kirigami.FormLayout {
                Layout.fillWidth: true
                visible: !root.importUnrecognized
                Label {
                    Kirigami.FormData.label: "File:"
                    text: "bitwarden_export.csv (Bitwarden)"
                }
                Label {
                    Kirigami.FormData.label: "New:"
                    text: "38 passwords"
                }
                Label {
                    Kirigami.FormData.label: "Already saved:"
                    text: "4 passwords are identical and are skipped"
                }
                Label {
                    Kirigami.FormData.label: "Different:"
                    text: "2 sites already have a different saved password"
                }
                CheckBox {
                    text: "Replace them with the imported passwords"
                    checked: false
                }
                Label {
                    Kirigami.FormData.label: "Not imported:"
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: "3 entries: 2 without an https:// website, 1 without a username or password"
                }
            }
        }
    }

    // ── Get New Extensions dialog (#107) ────────────────────────────────
    Dialog {
        parent: root
        anchors.centerIn: parent
        width: Kirigami.Units.gridUnit * 40
        height: Kirigami.Units.gridUnit * 28
        modal: true
        dim: true
        visible: root.catalogDialog
        title: "Get New Extensions"
        standardButtons: Dialog.Close

        contentItem: ColumnLayout {
            spacing: Kirigami.Units.largeSpacing
            TextField { Layout.fillWidth: true; placeholderText: "Search extensions…" }
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
                    model: ListModel {
                        ListElement { iconName: "weather-clear-night"; name: "Dark Mode"; author: "Kondor contributors"; desc: "Shows every site with dark colors."; entryState: "installed" }
                        ListElement { iconName: "text-x-script"; name: "User Scripts"; author: "Kondor contributors"; desc: "Install and manage user scripts that customize websites."; entryState: "install" }
                        ListElement { iconName: "preferences-web-browser-cookies"; name: "Cookie Banner Blocker"; author: "Kondor contributors"; desc: "Rejects or hides cookie consent banners."; entryState: "install" }
                        ListElement { iconName: "media-skip-forward"; name: "Skip Sponsors"; author: "Kondor contributors"; desc: "Skips sponsored segments in YouTube videos (SponsorBlock)."; entryState: "install" }
                        ListElement { iconName: "media-playback-start"; name: "Video Speed Controller"; author: "Kondor contributors"; desc: "Change the playback speed of any video with the keyboard."; entryState: "update" }
                    }
                    delegate: ItemDelegate {
                        required property string iconName
                        required property string name
                        required property string author
                        required property string desc
                        required property string entryState
                        width: ListView.view.width
                        contentItem: RowLayout {
                            spacing: Kirigami.Units.largeSpacing
                            Kirigami.Icon { source: iconName; Layout.preferredWidth: Kirigami.Units.iconSizes.large; Layout.preferredHeight: Layout.preferredWidth }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 0
                                RowLayout {
                                    Label { text: name; font.bold: true }
                                    Label { text: "by " + author; opacity: 0.7; font: Kirigami.Theme.smallFont }
                                }
                                Label { Layout.fillWidth: true; text: desc; wrapMode: Text.WordWrap }
                            }
                            Button {
                                text: entryState === "installed" ? "Installed" : entryState === "update" ? "Update" : "Install"
                                icon.name: entryState === "installed" ? "checkmark" : entryState === "update" ? "update-none" : "download"
                                enabled: entryState !== "installed"
                            }
                        }
                    }
                }
            }
            Label {
                text: "<a href=\"#\">Submit an extension…</a>"
                textFormat: Text.StyledText
                color: Kirigami.Theme.linkColor
            }
        }
    }

    // ── Install confirmation (#107) ─────────────────────────────────────
    Dialog {
        parent: root
        anchors.centerIn: parent
        width: Kirigami.Units.gridUnit * 26
        modal: true
        dim: true
        visible: root.installDialog
        title: "Install Extension"
        footer: DialogButtonBox {
            Button { text: "Install"; icon.name: "download"; DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole }
            Button { text: "Cancel"; icon.name: "dialog-cancel"; DialogButtonBox.buttonRole: DialogButtonBox.RejectRole }
        }

        contentItem: ColumnLayout {
            spacing: Kirigami.Units.largeSpacing
            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: root.installFromFile
                type: Kirigami.MessageType.Warning
                text: "This extension does not come from the Kondor extensions catalog. Only install extensions from people you trust."
            }
            RowLayout {
                spacing: Kirigami.Units.largeSpacing
                Kirigami.Icon { source: root.installFromFile ? "input-mouse" : "media-skip-forward"; Layout.preferredWidth: Kirigami.Units.iconSizes.large; Layout.preferredHeight: Layout.preferredWidth }
                Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: root.installFromFile ? "Install “Mouse Gestures” 0.3.0 by Maria Example?"
                                               : "Install “Skip Sponsors” 1.0.0 by Kondor contributors?"
                }
            }
            Label { text: "It will be able to:" }
            Repeater {
                model: root.installFromFile
                       ? [ { icon: "internet-services", text: "Read and change all websites" },
                           { icon: "tab-new", text: "Open, close and navigate your tabs" } ]
                       : [ { icon: "internet-services", text: "Read and change pages on www.youtube.com" } ]
                delegate: RowLayout {
                    required property var modelData
                    Layout.leftMargin: Kirigami.Units.largeSpacing
                    spacing: Kirigami.Units.smallSpacing
                    Kirigami.Icon { source: modelData.icon; Layout.preferredWidth: Kirigami.Units.iconSizes.small; Layout.preferredHeight: Layout.preferredWidth }
                    Label { text: modelData.text }
                }
            }
        }
    }
}
