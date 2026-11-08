// #3 Settings — "Configure Kondor" window (Ctrl+,): pages on the left, Kirigami.FormLayout on the right.
// Changes apply immediately (no OK/Apply), like KDE apps.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    width: 820
    height: 560
    color: Kirigami.Theme.backgroundColor

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Page list (like KConfigDialog / System Settings)
        ScrollView {
            Layout.preferredWidth: 200
            Layout.fillHeight: true
            Kirigami.Theme.colorSet: Kirigami.Theme.View
            Kirigami.Theme.inherit: false
            background: Rectangle { color: Kirigami.Theme.backgroundColor }
            ListView {
                model: [
                    { t: "General", i: "go-home" }, { t: "Search", i: "edit-find" }, { t: "Downloads", i: "download" },
                    { t: "Privacy", i: "security-high" }, { t: "Passwords", i: "dialog-password" },
                    { t: "Spelling", i: "tools-check-spelling" }
                ]
                delegate: ItemDelegate {
                    required property var modelData
                    required property int index
                    width: ListView.view.width
                    highlighted: index === 0
                    icon.name: modelData.i
                    text: modelData.t
                }
            }
        }
        Kirigami.Separator { Layout.fillHeight: true }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: Kirigami.Units.largeSpacing * 2
            spacing: Kirigami.Units.largeSpacing

            Kirigami.FormLayout {
                Layout.fillWidth: true

                Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: "On Startup" }
                RadioButton { Kirigami.FormData.label: "Open:"; text: "The home page"; checked: true }
                RadioButton { text: "The tabs from the previous session" }

                Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: "Home Page" }
                RowLayout {
                    Kirigami.FormData.label: "Address:"
                    TextField { text: "https://duckduckgo.com"; Layout.preferredWidth: 280 }
                    Button { text: "Use Current Page"; icon.name: "go-home" }
                }

                Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: "Search" }
                ComboBox { Kirigami.FormData.label: "Engine:"; model: ["DuckDuckGo", "Google", "Startpage", "Brave Search", "Custom…"]; Layout.preferredWidth: 280 }
                CheckBox { Kirigami.FormData.label: "Suggestions:"; text: "Show search engine suggestions" }

                Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: "Appearance" }
                CheckBox { Kirigami.FormData.label: "Toolbars:"; text: "Show bookmarks toolbar"; checked: true }
            }
            Item { Layout.fillHeight: true }
        }
    }
}
