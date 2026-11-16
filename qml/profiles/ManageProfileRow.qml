import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ItemDelegate {
    id: root

    required property var modelData
    required property int runningRevision

    readonly property bool isDefault: root.modelData.id === "default"
    readonly property bool isRunning: root.runningRevision >= 0 && UserProfiles.isRunning(root.modelData.id)

    signal editRequested(var profile)
    signal deleteRequested(var profile)

    width: ListView.view.width
    highlighted: ListView.isCurrentItem
    onClicked: ListView.view.currentIndex = index

    function deleteHint() {
        if (root.isDefault)
            return qsTr("The Default profile cannot be deleted")
        return root.isRunning ? qsTr("Close the windows of this profile first") : qsTr("Delete…")
    }

    contentItem: RowLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.Icon {
            source: root.modelData.iconName
            Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
            Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
        }

        Label {
            text: root.modelData.name
            elide: Text.ElideRight
            Layout.fillWidth: true
        }

        ToolButton {
            icon.name: "document-edit"
            display: AbstractButton.IconOnly
            text: qsTr("Edit %1").arg(root.modelData.name)
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Edit")
            ToolTip.delay: 600
            onClicked: root.editRequested(root.modelData)
        }

        Item {
            implicitWidth: deleteButton.implicitWidth
            implicitHeight: deleteButton.implicitHeight
            ToolTip.visible: deleteHover.hovered
            ToolTip.text: root.deleteHint()
            ToolTip.delay: 600

            HoverHandler { id: deleteHover }

            ToolButton {
                id: deleteButton
                icon.name: "edit-delete"
                display: AbstractButton.IconOnly
                enabled: !root.isDefault && !root.isRunning
                text: qsTr("Delete %1").arg(root.modelData.name)
                onClicked: root.deleteRequested(root.modelData)
            }
        }
    }
}
