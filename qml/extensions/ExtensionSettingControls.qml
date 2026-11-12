pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import org.kde.kirigami as Kirigami

Item {
    id: controls

    required property var values

    signal valueEdited(string key, var value)

    readonly property var byType: ({
        "bool": boolControl,
        "number": numberControl,
        "text": textControl,
        "choice": choiceControl,
        "color": colorControl
    })

    function componentFor(type) {
        return controls.byType[type] ?? stringControl
    }

    function indexOfChoice(choices, current) {
        return choices.findIndex(function(choice) { return choice.value === current })
    }

    Component {
        id: boolControl
        CheckBox {
            checked: controls.values[parent.modelData.key] === true
            onToggled: controls.valueEdited(parent.modelData.key, checked)
        }
    }

    Component {
        id: stringControl
        TextField {
            implicitWidth: Kirigami.Units.gridUnit * 16
            text: controls.values[parent.modelData.key] ?? ""
            onTextEdited: controls.valueEdited(parent.modelData.key, text)
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
                text: controls.values[textScroll.setting.key] ?? ""
                wrapMode: TextEdit.Wrap
                onTextChanged: if (text !== (controls.values[textScroll.setting.key] ?? ""))
                    controls.valueEdited(textScroll.setting.key, text)
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
            readonly property real current: Number(controls.values[setting.key] ?? setting.default ?? 0)

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
                    onMoved: controls.valueEdited(numberRow.setting.key, value)
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
                    onValueModified: controls.valueEdited(numberRow.setting.key, value)
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
            currentIndex: controls.indexOfChoice(choices, controls.values[parent.modelData.key])
            onActivated: function(index) { controls.valueEdited(parent.modelData.key, choices[index].value) }
        }
    }

    Component {
        id: colorControl
        Button {
            id: colorButton
            readonly property string key: parent.modelData.key
            text: controls.values[key] ?? ""
            icon.source: ""
            leftPadding: Kirigami.Units.gridUnit * 2
            Rectangle {
                anchors { left: parent.left; leftMargin: Kirigami.Units.smallSpacing; verticalCenter: parent.verticalCenter }
                width: Kirigami.Units.gridUnit
                height: width
                radius: 2
                color: controls.values[colorButton.key] ?? "transparent"
                border.color: Kirigami.Theme.textColor
            }
            onClicked: {
                colorDialog.targetKey = key
                colorDialog.selectedColor = controls.values[key] ?? "white"
                colorDialog.open()
            }
        }
    }

    ColorDialog {
        id: colorDialog
        property string targetKey: ""
        title: qsTr("Choose a Color")
        onAccepted: controls.valueEdited(colorDialog.targetKey, String(selectedColor))
    }
}
