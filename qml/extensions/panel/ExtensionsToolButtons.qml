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

    function pinnedExtensions(revision, pins) {
        return ExtensionManager.pinnedActionExtensions(isPrivate)
    }

    Repeater {
        model: root.pinnedExtensions(ExtensionManager.revision, Settings.pinnedExtensions)

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
            objectName: "extensionsPanel"
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
