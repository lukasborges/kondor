import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ColumnLayout {
    id: root

    required property var extension
    required property var tab
    required property string host

    readonly property bool isRightToLeft: Qt.application.layoutDirection === Qt.RightToLeft
    readonly property bool hasSiteSwitch: extension.siteToggle && ExtensionManager.originOf(tab.url) !== ""
    readonly property bool isPinned: (Settings.pinnedExtensions, ExtensionManager.isPinned(extension.id))

    signal backRequested()
    signal settingsRequested(string extensionId)

    function focusFirstAction() {
        const target = entries.count > 0 ? entries.itemAt(0) : backButton
        if (target.focusEntry)
            target.focusEntry()
        else
            target.forceActiveFocus()
    }

    function moveFocus(isForward) {
        const next = Window.window.activeFocusItem.nextItemInFocusChain(isForward)
        if (next)
            next.forceActiveFocus(isForward ? Qt.TabFocusReason : Qt.BacktabFocusReason)
    }

    function goBackOnBackspace(event) {
        if (event.key !== Qt.Key_Backspace)
            return
        event.accepted = true
        backRequested()
    }

    spacing: Kirigami.Units.smallSpacing
    Keys.onDownPressed: moveFocus(true)
    Keys.onUpPressed: moveFocus(false)
    Keys.onPressed: function(event) { goBackOnBackspace(event) }
    Keys.onLeftPressed: if (!isRightToLeft) backRequested()
    Keys.onRightPressed: if (isRightToLeft) backRequested()

    RowLayout {
        spacing: Kirigami.Units.smallSpacing

        ToolButton {
            id: backButton
            objectName: "backButton"
            display: AbstractButton.IconOnly
            icon.name: root.isRightToLeft ? "go-next" : "go-previous"
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Back to Extensions")
            ToolTip.delay: 600
            Accessible.name: ToolTip.text
            onClicked: root.backRequested()
        }

        Kirigami.Icon {
            source: root.extension.iconSource
            Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
            Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
        }

        Kirigami.Heading {
            level: 4
            text: root.extension.name
            elide: Text.ElideRight
            Layout.fillWidth: true
        }
    }

    Kirigami.Separator { Layout.fillWidth: true }

    Repeater {
        id: entries
        model: root.extension.items

        ExtensionActionEntry {
            extensionId: root.extension.id
            tab: root.tab
        }
    }

    Kirigami.Separator {
        visible: root.hasSiteSwitch
        Layout.fillWidth: true
    }

    ExtensionSiteSwitch {
        visible: root.hasSiteSwitch
        extension: root.extension
        tab: root.tab
        host: root.host
    }

    Kirigami.Separator { Layout.fillWidth: true }

    ExtensionActionsFooter {
        extension: root.extension
        isPinned: root.isPinned
        isPrivate: root.tab.isPrivate
        onSettingsRequested: function(extensionId) { root.settingsRequested(extensionId) }
    }
}
