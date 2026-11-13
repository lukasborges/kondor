import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ColumnLayout {
    id: root

    required property var extensions
    required property var tab
    required property string host

    signal extensionChosen(string extensionId)
    signal manageRequested()

    function focusRow(index) {
        const target = Math.max(0, Math.min(index, list.count - 1))
        list.positionViewAtIndex(target, ListView.Contain)
        list.currentIndex = target
        const row = list.itemAtIndex(target)
        if (row)
            row.forceActiveFocus()
    }

    function focusExtension(extensionId) {
        focusRow(extensions.findIndex(function(extension) { return extension.id === extensionId }))
    }

    spacing: Kirigami.Units.smallSpacing

    ColumnLayout {
        spacing: 0

        Kirigami.Heading {
            level: 4
            text: qsTr("Extensions")
        }

        Label {
            text: root.host
            visible: root.host !== ""
            color: Kirigami.Theme.disabledTextColor
        }
    }

    Kirigami.Separator { Layout.fillWidth: true }

    ScrollView {
        Layout.fillWidth: true
        Layout.preferredHeight: Math.min(list.contentHeight, Kirigami.Units.gridUnit * 18)

        ListView {
            id: list
            objectName: "panelExtensionList"
            model: root.extensions
            clip: true

            delegate: ExtensionRow {
                required property int index
                tab: root.tab
                host: root.host
                onOpenRequested: root.extensionChosen(modelData.id)
                onStepRequested: function(step) { root.focusRow(index + step) }
            }
        }
    }

    Kirigami.Separator { Layout.fillWidth: true }

    Button {
        text: qsTr("Manage Extensions…")
        icon.name: "configure"
        flat: true
        onClicked: root.manageRequested()
    }
}
