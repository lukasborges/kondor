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
    readonly property bool isOffHere: modelData.siteToggle
                                      && !isSiteEnabled(ExtensionManager.revision)

    signal openRequested()
    signal stepRequested(int step)

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

        Kirigami.Icon {
            source: root.isRightToLeft ? "go-previous" : "go-next"
            Layout.preferredWidth: Kirigami.Units.iconSizes.small
            Layout.preferredHeight: Kirigami.Units.iconSizes.small
        }
    }
}
