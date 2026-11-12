import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

InlineBar {
    id: root

    property Tab tab: null
    property var permission: tab ? tab.permissions.pending : null
    readonly property bool hasPermission: permission !== null && permission !== undefined

    visible: hasPermission

    PermissionTypeInfo {
        id: typeInfo
    }

    Kirigami.Icon {
        source: root.hasPermission ? typeInfo.iconFor(root.permission.permissionType) : ""
        Layout.preferredWidth: Kirigami.Units.iconSizes.small
        Layout.preferredHeight: Kirigami.Units.iconSizes.small
    }

    Label {
        Layout.fillWidth: true
        textFormat: Text.RichText
        text: root.hasPermission
              ? typeInfo.sentenceFor(root.permission.permissionType,
                                     typeInfo.hostFor(root.permission.origin))
              : ""
    }

    Button {
        text: qsTr("Allow")
        icon.name: "dialog-ok-apply"
        enabled: root.hasPermission
        ToolTip.visible: hovered
        ToolTip.text: qsTr("This decision is remembered for this site")
        ToolTip.delay: 600
        onClicked: {
            if (root.tab)
                root.tab.permissions.answer(true)
        }
    }

    Button {
        text: qsTr("Block")
        icon.name: "dialog-cancel"
        enabled: root.hasPermission
        ToolTip.visible: hovered
        ToolTip.text: qsTr("This decision is remembered for this site")
        ToolTip.delay: 600
        onClicked: {
            if (root.tab)
                root.tab.permissions.answer(false)
        }
    }
}
