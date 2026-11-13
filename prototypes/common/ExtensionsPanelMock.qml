// The toolbar Extensions panel: one row per extension (switch for this site, drill-down to its actions).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Popup {
    id: root
    property string host: "www.youtube.com"
    property var extensions: []
    default property alias page: pageSlot.data
    property bool showList: true

    popupType: Popup.Item
    closePolicy: Popup.NoAutoClose
    width: 380
    padding: Kirigami.Units.largeSpacing
    visible: true

    component ExtensionRow: ItemDelegate {
        id: row
        required property var modelData
        width: ListView.view.width
        padding: Kirigami.Units.smallSpacing
        contentItem: RowLayout {
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Icon {
                source: row.modelData.icon
                Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
            }
            Label { text: row.modelData.name; elide: Text.ElideRight; Layout.fillWidth: true }
            Switch {
                visible: row.modelData.siteToggle
                checked: row.modelData.on
                Accessible.name: "Run " + row.modelData.name + " on " + root.host
            }
            Item {
                visible: !row.modelData.siteToggle
                Layout.preferredWidth: Kirigami.Units.gridUnit * 2
            }
            Kirigami.Icon {
                source: "go-next"
                Layout.preferredWidth: Kirigami.Units.iconSizes.small
                Layout.preferredHeight: Kirigami.Units.iconSizes.small
            }
        }
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.smallSpacing
        ColumnLayout {
            visible: root.showList
            spacing: Kirigami.Units.smallSpacing
            RowLayout {
                spacing: Kirigami.Units.largeSpacing
                Kirigami.Heading { level: 4; text: "Extensions"; Layout.fillWidth: true }
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: Kirigami.Theme.disabledTextColor
                text: "Switch an extension on or off for " + root.host + "."
            }
            Kirigami.Separator { Layout.fillWidth: true }
            ScrollView {
                Layout.fillWidth: true
                Layout.preferredHeight: Math.min(list.contentHeight, Kirigami.Units.gridUnit * 18)
                ListView {
                    id: list
                    model: root.extensions
                    clip: true
                    delegate: ExtensionRow {}
                }
            }
            Kirigami.Separator { Layout.fillWidth: true }
            Button { text: "Manage Extensions…"; icon.name: "configure"; flat: true }
        }
        ColumnLayout {
            id: pageSlot
            visible: !root.showList
            spacing: Kirigami.Units.smallSpacing
        }
    }
}
