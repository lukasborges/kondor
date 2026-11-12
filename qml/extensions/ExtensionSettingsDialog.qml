pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import org.kde.kirigami as Kirigami
import Kondor

// "Configure…" of one extension: a form generated from the `settings` of its
// manifest, the "Allow in private windows" choice and the sites it is turned
// off on. The controls edit a pending copy; OK writes it to ExtensionManager.
Dialog {
    id: root

    property string extensionId: ""
    property var config: ({})
    // Pending values by setting key.
    property var values: ({})
    property bool privateAllowed: false
    property var sites: []

    readonly property var schema: root.config.settings ?? []

    function openFor(id) {
        root.extensionId = id
        root.config = ExtensionManager.configurationFor(id)
        const copy = {}
        for (const setting of root.schema)
            copy[setting.key] = setting.value
        root.values = copy
        root.privateAllowed = root.config.privateAllowed === true
        root.sites = (root.config.disabledSites ?? []).slice()
        root.open()
    }

    function setValue(key, value) {
        const copy = Object.assign({}, root.values)
        copy[key] = value
        root.values = copy
    }

    function restoreDefaults() {
        const copy = {}
        for (const setting of root.schema)
            copy[setting.key] = setting.default
        root.values = copy
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
                    sourceComponent: {
                        switch (field.modelData.type) {
                        case "bool": return boolControl
                        case "number": return numberControl
                        case "text": return textControl
                        case "choice": return choiceControl
                        case "color": return colorControl
                        default: return stringControl
                        }
                    }
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

        ColumnLayout {
            Layout.fillWidth: true
            visible: root.sites.length > 0
            spacing: Kirigami.Units.smallSpacing

            Label {
                text: qsTr("Turned off on:")
            }

            Repeater {
                model: root.sites

                delegate: RowLayout {
                    id: siteRow
                    required property string modelData
                    Layout.fillWidth: true
                    Layout.leftMargin: Kirigami.Units.largeSpacing

                    Label {
                        Layout.fillWidth: true
                        text: siteRow.modelData
                        elide: Text.ElideMiddle
                    }
                    ToolButton {
                        icon.name: "list-remove"
                        text: qsTr("Remove")
                        display: AbstractButton.TextBesideIcon
                        onClicked: root.sites = root.sites.filter(function(site) {
                            return site !== siteRow.modelData
                        })
                    }
                }
            }
        }
    }

    // ── Controls by setting type ─────────────────────────────────────────
    // Each is created inside the Loader of its form row, so `field` is the
    // setting object of that row.
    Component {
        id: boolControl
        CheckBox {
            checked: root.values[parent.modelData.key] === true
            onToggled: root.setValue(parent.modelData.key, checked)
        }
    }

    Component {
        id: stringControl
        TextField {
            implicitWidth: Kirigami.Units.gridUnit * 16
            text: root.values[parent.modelData.key] ?? ""
            onTextEdited: root.setValue(parent.modelData.key, text)
        }
    }

    Component {
        id: textControl
        ScrollView {
            id: textScroll
            readonly property var setting: parent.modelData
            implicitWidth: Kirigami.Units.gridUnit * 20
            implicitHeight: Kirigami.Units.gridUnit * 6
            TextArea {
                text: root.values[textScroll.setting.key] ?? ""
                wrapMode: TextEdit.Wrap
                onTextChanged: if (text !== (root.values[textScroll.setting.key] ?? ""))
                    root.setValue(textScroll.setting.key, text)
            }
        }
    }

    Component {
        id: numberControl
        RowLayout {
            id: numberRow
            readonly property var setting: parent.modelData
            readonly property real minValue: setting.min ?? 0
            readonly property real maxValue: setting.max ?? 100
            readonly property real stepValue: setting.step ?? 1
            readonly property string suffix: setting.suffix ?? ""
            readonly property real current: Number(root.values[setting.key] ?? setting.default ?? 0)

            Loader {
                sourceComponent: numberRow.maxValue - numberRow.minValue <= 200 ? sliderControl : spinControl
            }
            Label {
                visible: numberRow.maxValue - numberRow.minValue <= 200
                text: numberRow.current + numberRow.suffix
            }
            Component {
                id: sliderControl
                Slider {
                    implicitWidth: Kirigami.Units.gridUnit * 12
                    from: numberRow.minValue
                    to: numberRow.maxValue
                    stepSize: numberRow.stepValue
                    value: numberRow.current
                    onMoved: root.setValue(numberRow.setting.key, value)
                }
            }
            Component {
                id: spinControl
                SpinBox {
                    editable: true
                    from: numberRow.minValue
                    to: numberRow.maxValue
                    stepSize: numberRow.stepValue
                    value: numberRow.current
                    textFromValue: function(value) { return value + numberRow.suffix }
                    valueFromText: function(text) { return parseInt(text) }
                    onValueModified: root.setValue(numberRow.setting.key, value)
                }
            }
        }
    }

    Component {
        id: choiceControl
        ComboBox {
            readonly property var choices: parent.modelData.choices ?? []
            implicitWidth: Kirigami.Units.gridUnit * 12
            model: choices
            textRole: "label"
            currentIndex: {
                const current = root.values[parent.modelData.key]
                for (let i = 0; i < choices.length; ++i) {
                    if (choices[i].value === current)
                        return i
                }
                return -1
            }
            onActivated: function(index) { root.setValue(parent.modelData.key, choices[index].value) }
        }
    }

    Component {
        id: colorControl
        Button {
            id: colorButton
            readonly property string key: parent.modelData.key
            text: root.values[key] ?? ""
            icon.source: ""
            leftPadding: Kirigami.Units.gridUnit * 2
            Rectangle {
                anchors { left: parent.left; leftMargin: Kirigami.Units.smallSpacing; verticalCenter: parent.verticalCenter }
                width: Kirigami.Units.gridUnit
                height: width
                radius: 2
                color: root.values[colorButton.key] ?? "transparent"
                border.color: Kirigami.Theme.textColor
            }
            onClicked: {
                colorDialog.targetKey = key
                colorDialog.selectedColor = root.values[key] ?? "white"
                colorDialog.open()
            }
        }
    }

    ColorDialog {
        id: colorDialog
        property string targetKey: ""
        title: qsTr("Choose a Color")
        onAccepted: root.setValue(colorDialog.targetKey, String(selectedColor))
    }
}
