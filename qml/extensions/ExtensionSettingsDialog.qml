pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Dialog {
    id: root

    property string extensionId: ""
    property var config: ({})
    property var values: ({})
    property bool privateAllowed: false
    property var sites: []

    readonly property var schema: root.config.settings ?? []

    function openFor(id) {
        root.extensionId = id
        root.config = ExtensionManager.configurationFor(id)
        root.values = valuesFrom("value")
        root.privateAllowed = root.config.privateAllowed === true
        root.sites = (root.config.disabledSites ?? []).slice()
        root.open()
    }

    function valuesFrom(property) {
        const copy = {}
        for (const setting of root.schema)
            copy[setting.key] = setting[property]
        return copy
    }

    function setValue(key, value) {
        const copy = Object.assign({}, root.values)
        copy[key] = value
        root.values = copy
    }

    function restoreDefaults() {
        root.values = valuesFrom("default")
    }

    function removeSite(site) {
        root.sites = root.sites.filter(function(other) { return other !== site })
    }

    function accept() {
        ExtensionManager.applyConfiguration(root.extensionId, {settings: root.values,
            privateAllowed: root.privateAllowed, disabledSites: root.sites})
        root.close()
    }

    anchors.centerIn: parent
    width: Kirigami.Units.gridUnit * 30
    modal: true
    dim: true
    closePolicy: Popup.CloseOnEscape
    //: %1 is the name of an extension
    title: qsTr("Configure — %1").arg(root.config.name ?? "")

    footer: DialogButtonBox {
        Button {
            visible: root.schema.length > 0
            text: qsTr("Restore Defaults")
            icon.name: "document-revert"
            DialogButtonBox.buttonRole: DialogButtonBox.ResetRole
            onClicked: root.restoreDefaults()
        }
        Button {
            text: qsTr("OK")
            icon.name: "dialog-ok"
            highlighted: true
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            onClicked: root.accept()
        }
        Button {
            text: qsTr("Cancel")
            icon.name: "dialog-cancel"
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            onClicked: root.close()
        }
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.FormLayout {
            Layout.fillWidth: true
            visible: root.schema.length > 0

            Repeater {
                model: root.schema

                delegate: Loader {
                    id: field
                    required property var modelData
                    Kirigami.FormData.label: field.modelData.label + ":"
                    Layout.fillWidth: true
                    sourceComponent: controls.componentFor(field.modelData.type)
                }
            }
        }

        Kirigami.FormLayout {
            Layout.fillWidth: true

            Kirigami.Separator {
                Kirigami.FormData.isSection: true
                Kirigami.FormData.label: qsTr("Privacy")
            }

            CheckBox {
                text: qsTr("Allow in private windows")
                checked: root.privateAllowed
                onToggled: root.privateAllowed = checked
            }
        }

        ExtensionSitesSection {
            Layout.fillWidth: true
            sites: root.sites
            onSiteRemoved: function(site) { root.removeSite(site) }
        }

        ExtensionSettingControls {
            id: controls
            visible: false
            values: root.values
            onValueEdited: function(key, value) { root.setValue(key, value) }
        }
    }
}
