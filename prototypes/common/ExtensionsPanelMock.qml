// The toolbar Extensions panel: one row per extension ("Off on this site" when off), drill-down to its actions.
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
        Accessible.name: row.modelData.siteToggle && !row.modelData.on
                         ? row.modelData.name + ", off on " + root.host : row.modelData.name
        contentItem: RowLayout {
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Icon {
                source: row.modelData.icon
                Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
            }
            Label { text: row.modelData.name; elide: Text.ElideRight; Layout.fillWidth: true }
            Label {
                visible: row.modelData.siteToggle && !row.modelData.on
                text: "Off on this site"
                color: Kirigami.Theme.disabledTextColor
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
            ColumnLayout {
                spacing: 0
                Kirigami.Heading { level: 4; text: "Extensions" }
                Label { text: root.host; color: Kirigami.Theme.disabledTextColor }
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
