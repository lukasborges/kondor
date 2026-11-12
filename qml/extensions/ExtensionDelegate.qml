pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ItemDelegate {
    id: row

    required property string id
    required property string name
    required property string description
    required property string version
    required property string iconSource
    required property var model
    required property var permissions
    required property bool updateNeedsReview
    property string filterText: ""

    signal configureRequested(string id)
    signal removeRequested(string id, string name)

    function matchesFilter() {
        const text = row.filterText.trim().toLowerCase()
        return text === "" || (row.name + " " + row.description).toLowerCase().includes(text)
    }

    width: ListView.view.width
    visible: row.matchesFilter()
    height: visible ? implicitHeight : 0
    hoverEnabled: false
    down: false

    contentItem: RowLayout {
        spacing: Kirigami.Units.largeSpacing

        ExtensionIcon {
            source: row.iconSource
            size: Kirigami.Units.iconSizes.medium
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0

            RowLayout {
                Label {
                    text: row.name
                    font.bold: true
                }
                Label {
                    text: row.version
                    opacity: 0.7
                    font: Kirigami.Theme.smallFont
                }
            }
            Label {
                Layout.fillWidth: true
                text: row.description
                elide: Text.ElideRight
            }
            Label {
                Layout.fillWidth: true
                visible: row.permissions.length > 0
                text: row.permissions.length > 0 ? row.permissions[0] : ""
                opacity: 0.7
                font: Kirigami.Theme.smallFont
                elide: Text.ElideRight
            }
        }

        Button {
            visible: row.updateNeedsReview
            text: qsTr("Update…")
            icon.name: "update-none"
            onClicked: ExtensionCatalog.install(row.id)
        }
        Switch {
            checked: row.model.enabled
            onToggled: ExtensionManager.setEnabled(row.id, checked)
            ToolTip.visible: hovered
            ToolTip.text: row.model.enabled ? qsTr("Turn off") : qsTr("Turn on")
            ToolTip.delay: 600
        }
        ToolButton {
            icon.name: "configure"
            text: qsTr("Configure…")
            display: AbstractButton.IconOnly
            ToolTip.visible: hovered
            ToolTip.text: text
            ToolTip.delay: 600
            onClicked: row.configureRequested(row.id)
        }
        ToolButton {
            icon.name: "edit-delete"
            text: qsTr("Remove")
            display: AbstractButton.IconOnly
            ToolTip.visible: hovered
            ToolTip.text: text
            ToolTip.delay: 600
            onClicked: row.removeRequested(row.id, row.name)
        }
    }
}
