// #191 Saved Passwords panel with a search field. Static mock of the #176 panel plus search:
// "site" (empty search, this site's accounts), "search" (results from every site), "empty"
// (no login for this site) and "noMatches".
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Popup {
    id: panel

    property string level: "site"
    property string query: ""
    property string host: "accounts.example.org"
    property var siteAccounts: []
    property var results: []

    popupType: Popup.Item
    width: 360
    padding: Kirigami.Units.largeSpacing
    Component.onCompleted: open()

    component CopyButtons: RowLayout {
        property string username
        spacing: Kirigami.Units.smallSpacing
        ToolButton {
            icon.name: "edit-copy"
            icon.width: Kirigami.Units.iconSizes.smallMedium
            icon.height: Kirigami.Units.iconSizes.smallMedium
            display: AbstractButton.IconOnly
            ToolTip.text: "Copy Username"
            ToolTip.delay: 600
            Accessible.name: "Copy Username for " + parent.username
        }
        ToolButton {
            icon.name: "password-copy"
            icon.width: Kirigami.Units.iconSizes.smallMedium
            icon.height: Kirigami.Units.iconSizes.smallMedium
            display: AbstractButton.IconOnly
            ToolTip.text: "Copy Password"
            ToolTip.delay: 600
            Accessible.name: "Copy Password for " + parent.username
        }
    }

    component AccountRow: ItemDelegate {
        id: accountRow
        required property string username
        Layout.fillWidth: true
        padding: Kirigami.Units.smallSpacing
        contentItem: RowLayout {
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Icon {
                source: "user-identity"
                Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
            }
            Label { text: accountRow.username; elide: Text.ElideRight; Layout.fillWidth: true }
            CopyButtons { username: accountRow.username }
        }
    }

    component ResultRow: ItemDelegate {
        id: resultRow
        required property var modelData
        width: ListView.view ? ListView.view.width - resultsScrollBar.width : implicitWidth
        padding: Kirigami.Units.smallSpacing
        highlighted: ListView.isCurrentItem
        contentItem: RowLayout {
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Icon {
                source: resultRow.modelData.icon
                Layout.preferredWidth: Kirigami.Units.iconSizes.small
                Layout.preferredHeight: Kirigami.Units.iconSizes.small
                Layout.leftMargin: Kirigami.Units.smallSpacing / 2
                Layout.rightMargin: Kirigami.Units.smallSpacing / 2
            }
            ColumnLayout {
                spacing: 0
                Layout.fillWidth: true
                Label { text: resultRow.modelData.host; elide: Text.ElideRight; Layout.fillWidth: true }
                Label {
                    text: resultRow.modelData.username
                    elide: Text.ElideRight
                    color: Kirigami.Theme.disabledTextColor
                    font: Kirigami.Theme.smallFont
                    Layout.fillWidth: true
                }
            }
            CopyButtons { username: resultRow.modelData.username }
        }
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.smallSpacing

        RowLayout {
            spacing: Kirigami.Units.largeSpacing
            Kirigami.Icon { source: "dialog-password"; Layout.preferredWidth: 32; Layout.preferredHeight: 32 }
            ColumnLayout {
                spacing: 0
                Kirigami.Heading { level: 4; text: "Saved Passwords" }
                Label { text: panel.host; color: Kirigami.Theme.disabledTextColor }
            }
        }

        TextField {
            Layout.fillWidth: true
            placeholderText: "Search passwords"
            text: panel.query
            focus: true
            leftPadding: Kirigami.Units.iconSizes.small + Kirigami.Units.largeSpacing
            Kirigami.Icon {
                source: "edit-find"
                x: Kirigami.Units.smallSpacing
                width: Kirigami.Units.iconSizes.small
                height: Kirigami.Units.iconSizes.small
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        Repeater {
            model: panel.level === "site" ? panel.siteAccounts : []
            AccountRow {
                required property string modelData
                required property int index
                username: modelData
                highlighted: index === 0
            }
        }

        ListView {
            visible: panel.level === "search"
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(contentHeight, Kirigami.Units.gridUnit * 18)
            clip: true
            model: panel.results
            currentIndex: 0
            delegate: ResultRow {}
            ScrollBar.vertical: ScrollBar { id: resultsScrollBar }
        }

        Kirigami.PlaceholderMessage {
            visible: panel.level === "empty" || panel.level === "noMatches"
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.largeSpacing
            text: panel.level === "empty" ? "No Passwords for This Site" : "No Matches"
        }

        Kirigami.Separator { Layout.fillWidth: true }

        Button { text: "Manage Passwords…"; icon.name: "configure"; flat: true }
    }
}
