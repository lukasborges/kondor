import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ItemDelegate {
    id: root

    required property var modelData
    required property var tab
    required property string host

    readonly property bool isRightToLeft: Qt.application.layoutDirection === Qt.RightToLeft
    readonly property bool isPinned: isExtensionPinned(Settings.pinnedExtensions)
    readonly property bool isOffHere: modelData.siteToggle
                                      && !isSiteEnabled(ExtensionManager.revision)

    signal openRequested()
    signal stepRequested(int step)

    function isExtensionPinned(pins) {
        return ExtensionManager.isPinned(modelData.id)
    }

    function pinToggleName() {
        if (isPinned)
            //: %1 is the extension name
            return qsTr("Unpin %1 from Toolbar").arg(modelData.name)
        //: %1 is the extension name
        return qsTr("Pin %1 to Toolbar").arg(modelData.name)
    }

    function isSiteEnabled(revision) {
        return ExtensionManager.siteEnabled(modelData.id, tab.url)
    }

    width: ListView.view ? ListView.view.width : implicitWidth
    padding: Kirigami.Units.smallSpacing
    ToolTip.visible: hovered && isOffHere
    ToolTip.text: qsTr("Off on this site")
    ToolTip.delay: 600
    //: %1 is the extension name, %2 is the site host
    Accessible.name: isOffHere ? qsTr("%1, off on %2").arg(modelData.name).arg(host) : modelData.name
    onClicked: openRequested()
    Keys.onReturnPressed: openRequested()
    Keys.onEnterPressed: openRequested()
    Keys.onRightPressed: if (!isRightToLeft) openRequested()
    Keys.onLeftPressed: if (isRightToLeft) openRequested()
    Keys.onDownPressed: stepRequested(1)
    Keys.onUpPressed: stepRequested(-1)

    contentItem: RowLayout {
        spacing: Kirigami.Units.smallSpacing

        Kirigami.Icon {
            source: root.modelData.iconSource
            enabled: !root.isOffHere
            Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
            Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
        }

        Label {
            text: root.modelData.name
            enabled: !root.isOffHere
            elide: Text.ElideRight
            Layout.fillWidth: true
        }

        ToolButton {
            id: pinToggle
            objectName: "rowPinButton"
            visible: !root.tab.isPrivate
            display: AbstractButton.IconOnly
            icon.name: "window-pin"
            checkable: true
            checked: root.isPinned
            ToolTip.visible: hovered
            ToolTip.text: root.isPinned ? qsTr("Unpin from Toolbar") : qsTr("Pin to Toolbar")
            ToolTip.delay: 600
            Accessible.name: root.pinToggleName()
            Keys.onDownPressed: root.stepRequested(1)
            Keys.onUpPressed: root.stepRequested(-1)
            KeyNavigation.backtab: root
            onToggled: {
                ExtensionManager.setPinned(root.modelData.id, !root.isPinned)
                checked = Qt.binding(function() { return root.isPinned })
            }
        }

        Kirigami.Icon {
            source: root.isRightToLeft ? "go-previous" : "go-next"
            Layout.preferredWidth: Kirigami.Units.iconSizes.small
            Layout.preferredHeight: Kirigami.Units.iconSizes.small
        }
    }
}
