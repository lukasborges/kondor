import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Popup {
    id: editor

    required property TabModel tabModel
    property QtObject group: null

    readonly property bool isCollapsed: group !== null && group.collapsed
    readonly property var colorChoices: [
        { name: "blue", label: qsTr("Blue") },
        { name: "green", label: qsTr("Green") },
        { name: "orange", label: qsTr("Orange") },
        { name: "red", label: qsTr("Red") },
        { name: "purple", label: qsTr("Purple") },
        { name: "gray", label: qsTr("Gray") }
    ]

    signal newTabRequested(QtObject group)
    signal moveToNewWindowRequested(QtObject group)
    signal closeGroupRequested(QtObject group)

    popupType: Popup.Item
    width: Kirigami.Units.gridUnit * 16
    padding: Kirigami.Units.largeSpacing
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    function runAndClose(action) {
        const target = group
        close()
        action(target)
    }

    onOpened: {
        nameField.text = group ? group.name : ""
        nameField.forceActiveFocus()
        nameField.selectAll()
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        TextField {
            id: nameField
            Layout.fillWidth: true
            placeholderText: qsTr("Group name")
            Accessible.name: placeholderText
            onTextEdited: editor.group.setName(text)
            onAccepted: editor.close()
        }

        RowLayout {
            spacing: Kirigami.Units.smallSpacing

            Repeater {
                model: editor.colorChoices

                delegate: GroupSwatch {
                    required property var modelData
                    colorName: modelData.name
                    text: modelData.label
                    checked: editor.group !== null && editor.group.color === modelData.name
                    onClicked: editor.group.setColor(modelData.name)
                }
            }
        }

        Kirigami.Separator { Layout.fillWidth: true }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0

            ItemDelegate {
                Layout.fillWidth: true
                text: qsTr("New Tab in Group")
                icon.name: "tab-new"
                onClicked: editor.runAndClose(editor.newTabRequested)
            }
            ItemDelegate {
                Layout.fillWidth: true
                text: editor.isCollapsed ? qsTr("Expand Group") : qsTr("Collapse Group")
                icon.name: editor.isCollapsed ? "arrow-down" : "arrow-up"
                onClicked: editor.runAndClose(group => editor.tabModel.setGroupCollapsed(group, !group.collapsed))
            }
            ItemDelegate {
                Layout.fillWidth: true
                text: qsTr("Move Group to New Window")
                icon.name: "window-new"
                onClicked: editor.runAndClose(editor.moveToNewWindowRequested)
            }
            ItemDelegate {
                Layout.fillWidth: true
                text: qsTr("Ungroup Tabs")
                icon.name: "object-ungroup"
                onClicked: editor.runAndClose(editor.tabModel.ungroup)
            }
            ItemDelegate {
                Layout.fillWidth: true
                text: qsTr("Close Group")
                icon.name: "tab-close"
                onClicked: editor.runAndClose(editor.closeGroupRequested)
            }
        }
    }
}
