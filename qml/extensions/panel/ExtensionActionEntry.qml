import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: root

    required property var modelData
    required property string extensionId
    required property var tab

    property int stateRevision: 0

    function focusEntry() {
        (holder.item.checkBox ?? holder.item).forceActiveFocus()
    }

    function isItemChecked(revision) {
        return tab.extensionItems.isChecked(extensionId, modelData.id)
    }

    Layout.fillWidth: true
    implicitHeight: holder.implicitHeight

    Connections {
        target: root.tab.extensionItems
        function onChanged() { root.stateRevision++ }
    }

    Component {
        id: plainRow

        ExtensionActionRow {
            item: root.modelData
            extensionId: root.extensionId
            tab: root.tab
        }
    }

    Component {
        id: checkRow

        RowLayout {
            property alias checkBox: box

            CheckBox {
                id: box
                leftPadding: Kirigami.Units.smallSpacing
                text: root.modelData.title
                checked: root.isItemChecked(root.stateRevision)
                Accessible.description: root.modelData.shortcut ?? ""
                onToggled: root.tab.extensionItems.trigger(root.extensionId, root.modelData.id, true)
                Layout.fillWidth: true
            }

            Label {
                text: root.modelData.shortcut ?? ""
                color: Kirigami.Theme.disabledTextColor
                visible: text !== ""
                Layout.rightMargin: Kirigami.Units.smallSpacing
            }
        }
    }

    Loader {
        id: holder
        anchors.fill: parent
        sourceComponent: root.modelData.checkable ? checkRow : plainRow
    }
}
