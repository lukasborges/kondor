pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import org.kde.kirigami as Kirigami
import Kondor

// "Configure Kondor" window (Ctrl+,). Pages in a TabBar, one Kirigami.FormLayout
// each. Changes apply immediately, like KDE apps.
ApplicationWindow {
    id: root
    width: 640
    height: 520
    minimumWidth: 560
    minimumHeight: 420
    title: qsTr("Configure — Kondor")
    visible: false

    required property TabModel tabModel

    onClosing: function(close) {
        // Do not destroy: just hide, so it reopens with the same page.
        close.accepted = false
        root.visible = false
    }

    function showWindow() {
        root.visible = true
        root.raise()
        root.requestActivate()
    }

    // FolderDialog hands a file:// URL to QML; Settings stores a local path.
    function localPath(url) {
        let path = url.toString()
        if (path.startsWith("file://"))
            path = path.slice(7)
        return decodeURIComponent(path)
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TabBar {
            id: settingsTabBar
            Layout.fillWidth: true
            currentIndex: 0

            TabButton { text: qsTr("General") }
            TabButton { text: qsTr("Search") }
            TabButton { text: qsTr("Downloads") }
            TabButton { text: qsTr("Privacy") }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: settingsTabBar.currentIndex

            // ── General ──────────────────────────────────────────────────
            ScrollView {
                id: generalPage
                contentWidth: availableWidth
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                ColumnLayout {
                    width: generalPage.availableWidth
                    spacing: Kirigami.Units.largeSpacing

                    Kirigami.FormLayout {
                        Layout.fillWidth: true
                        Layout.margins: Kirigami.Units.gridUnit * 2

                        Kirigami.Separator {
                            Kirigami.FormData.isSection: true
                            Kirigami.FormData.label: qsTr("On Startup")
                        }

                        ComboBox {
                            id: startupBox
                            Kirigami.FormData.label: qsTr("Open:")
                            Layout.preferredWidth: Kirigami.Units.gridUnit * 20
                            model: [
                                { value: "homepage", label: qsTr("The home page") },
                                { value: "restore", label: qsTr("The tabs from the previous session") }
                            ]
                            textRole: "label"
                            valueRole: "value"
                            currentIndex: Settings.startupBehavior === "restore" ? 1 : 0
                            onActivated: Settings.startupBehavior = currentValue
                        }

                        Kirigami.Separator {
                            Kirigami.FormData.isSection: true
                            Kirigami.FormData.label: qsTr("Home Page")
                        }

                        RowLayout {
                            Kirigami.FormData.label: qsTr("Address:")

                            TextField {
                                id: homeField
                                Layout.preferredWidth: Kirigami.Units.gridUnit * 20
                                text: Settings.homePage
                                placeholderText: "https://duckduckgo.com"
                                onEditingFinished: {
                                    // Normalize "example.com" into "https://example.com".
                                    Settings.homePage = ProfileManager.resolveAddress(text).toString()
                                    text = Settings.homePage
                                }
                            }

                            Button {
                                text: qsTr("Use Current Page")
                                icon.name: "go-home"
                                // A private tab's URL must never land on disk.
                                enabled: root.tabModel.currentTab !== null
                                         && !root.tabModel.currentTab.isPrivate
                                onClicked: {
                                    const tab = root.tabModel.currentTab
                                    if (!tab)
                                        return
                                    Settings.homePage = tab.url.toString()
                                    homeField.text = Settings.homePage
                                }
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            // ── Search ───────────────────────────────────────────────────
            ScrollView {
                id: searchPage
                contentWidth: availableWidth
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                ColumnLayout {
                    width: searchPage.availableWidth
                    spacing: Kirigami.Units.largeSpacing

                    Kirigami.FormLayout {
                        Layout.fillWidth: true
                        Layout.margins: Kirigami.Units.gridUnit * 2

                        Kirigami.Separator {
                            Kirigami.FormData.isSection: true
                            Kirigami.FormData.label: qsTr("Search")
                        }

                        ComboBox {
                            id: engineBox
                            Kirigami.FormData.label: qsTr("Engine:")
                            Layout.preferredWidth: Kirigami.Units.gridUnit * 20
                            model: [
                                { value: "duckduckgo", label: "DuckDuckGo" },
                                { value: "google", label: "Google" },
                                { value: "startpage", label: "Startpage" },
                                { value: "brave", label: "Brave Search" },
                                { value: "custom", label: qsTr("Custom…") }
                            ]
                            textRole: "label"
                            valueRole: "value"
                            currentIndex: {
                                const index = indexOfValue(Settings.searchEngine)
                                return index >= 0 ? index : 0
                            }
                            onActivated: Settings.searchEngine = currentValue
                        }

                        TextField {
                            id: customField
                            Kirigami.FormData.label: qsTr("Custom URL:")
                            Layout.preferredWidth: Kirigami.Units.gridUnit * 28
                            enabled: Settings.searchEngine === "custom"
                            text: Settings.customSearchUrl
                            placeholderText: "https://www.bing.com/search?q=%1"
                            onEditingFinished: {
                                Settings.customSearchUrl = text
                                text = Settings.customSearchUrl
                            }
                        }
                    }

                    Kirigami.InlineMessage {
                        Layout.fillWidth: true
                        Layout.leftMargin: Kirigami.Units.gridUnit * 2
                        Layout.rightMargin: Kirigami.Units.gridUnit * 2
                        visible: Settings.searchEngine === "custom"
                                 && customField.text.indexOf("%1") === -1
                        type: Kirigami.MessageType.Warning
                        text: qsTr("The URL must contain “%1” where the search terms go.").arg("%1")
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            // ── Downloads ────────────────────────────────────────────────
            ScrollView {
                id: downloadsPage
                contentWidth: availableWidth
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                ColumnLayout {
                    width: downloadsPage.availableWidth
                    spacing: Kirigami.Units.largeSpacing

                    Kirigami.FormLayout {
                        Layout.fillWidth: true
                        Layout.margins: Kirigami.Units.gridUnit * 2

                        Kirigami.Separator {
                            Kirigami.FormData.isSection: true
                            Kirigami.FormData.label: qsTr("Downloads")
                        }

                        RowLayout {
                            Kirigami.FormData.label: qsTr("Folder:")

                            TextField {
                                id: downloadField
                                Layout.preferredWidth: Kirigami.Units.gridUnit * 20
                                text: Settings.downloadDirectory
                                readOnly: true
                                selectByMouse: true
                            }

                            Button {
                                text: qsTr("Choose…")
                                icon.name: "folder-open"
                                onClicked: downloadFolderDialog.open()
                            }
                        }

                        CheckBox {
                            Kirigami.FormData.label: qsTr("Saving:")
                            text: qsTr("Ask where to save each file")
                            checked: Settings.askWhereToSave
                            onToggled: Settings.askWhereToSave = checked
                        }
                    }

                    Kirigami.InlineMessage {
                        Layout.fillWidth: true
                        Layout.leftMargin: Kirigami.Units.gridUnit * 2
                        Layout.rightMargin: Kirigami.Units.gridUnit * 2
                        visible: !Settings.downloadDirectoryValid()
                        type: Kirigami.MessageType.Warning
                        text: qsTr("The selected folder no longer exists. Downloads are saved to %1.")
                                  .arg(Settings.downloadDirectory)
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            // ── Privacy ──────────────────────────────────────────────────
            ScrollView {
                id: privacyPage
                contentWidth: availableWidth
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                ColumnLayout {
                    width: privacyPage.availableWidth
                    spacing: Kirigami.Units.largeSpacing

                    Kirigami.FormLayout {
                        Layout.fillWidth: true
                        Layout.margins: Kirigami.Units.gridUnit * 2

                        Kirigami.Separator {
                            Kirigami.FormData.isSection: true
                            Kirigami.FormData.label: qsTr("Privacy")
                        }

                        CheckBox {
                            Kirigami.FormData.label: qsTr("Cookies:")
                            text: qsTr("Block third-party cookies")
                            checked: Settings.blockThirdPartyCookies
                            onToggled: Settings.blockThirdPartyCookies = checked
                        }

                        CheckBox {
                            Kirigami.FormData.label: qsTr("On Exit:")
                            text: qsTr("Clear cookies, cache and history")
                            checked: Settings.clearDataOnExit
                            onToggled: Settings.clearDataOnExit = checked
                        }

                        Button {
                            Kirigami.FormData.label: qsTr("Data:")
                            text: qsTr("Clear Cookies and Cache Now")
                            icon.name: "edit-clear"
                            onClicked: ProfileManager.clearCookiesAndCacheNow()
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }
        }
    }

    FolderDialog {
        id: downloadFolderDialog
        title: qsTr("Choose Download Folder")
        currentFolder: "file://" + Settings.downloadDirectory
        onAccepted: Settings.downloadDirectory = root.localPath(selectedFolder)
    }
}
