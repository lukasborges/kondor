import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kondor

RowLayout {
    id: root

    required property TabModel tabs
    required property var browserWindow

    readonly property bool isPrivate: tabs.currentTab ? tabs.currentTab.isPrivate : false

    spacing: 0
    visible: tabs.currentTab !== null
             && (ExtensionManager.revision, ExtensionManager.hasActionExtensions(isPrivate))

    Repeater {
        model: (ExtensionManager.revision, Settings.pinnedExtensions,
                ExtensionManager.pinnedActionExtensions(root.isPrivate))

        PinnedExtensionButton {
            onClicked: panel.openAt(modelData.id)
        }
    }

    ToolButton {
        id: extensionsButton
        objectName: "extensionsButton"
        display: AbstractButton.IconOnly
        icon.name: "plugins"
        checked: panel.opened
        ToolTip.visible: hovered
        Accessible.name: ToolTip.text
        ToolTip.text: qsTr("Extensions")
        ToolTip.delay: 600
        onClicked: panel.opened ? panel.close() : panel.open()

        ExtensionsPanel {
            id: panel
            tab: root.tabs.currentTab
            onManageRequested: root.browserWindow.openSettingsPage("extensions")
            onSettingsRequested: function(extensionId) { settingsDialog.openFor(extensionId) }
        }
    }

    ExtensionSettingsDialog {
        id: settingsDialog
        parent: Overlay.overlay
    }
}
