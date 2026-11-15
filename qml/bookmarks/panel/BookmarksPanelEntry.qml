import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ItemDelegate {
    id: root

    required property var modelData
    required property int index

    readonly property bool isRightToLeft: Qt.application.layoutDirection === Qt.RightToLeft

    signal openRequested(bool background)
    signal stepRequested(int step)

    function isBackgroundKey(event) {
        return (event.modifiers & Qt.ControlModifier) !== 0
    }

    function openFolder() {
        if (modelData.isFolder)
            openRequested(false)
    }

    width: ListView.view ? ListView.view.width : implicitWidth
    highlighted: ListView.isCurrentItem
    padding: Kirigami.Units.smallSpacing
    ToolTip.visible: hovered && modelData.url !== ""
    ToolTip.text: modelData.url
    ToolTip.delay: 600
    Accessible.name: modelData.title
    onClicked: openRequested(BookmarkManager.ctrlPressed())
    Keys.onReturnPressed: function(event) { openRequested(isBackgroundKey(event)) }
    Keys.onEnterPressed: function(event) { openRequested(isBackgroundKey(event)) }
    Keys.onRightPressed: if (!isRightToLeft) openFolder()
    Keys.onLeftPressed: if (isRightToLeft) openFolder()
    Keys.onDownPressed: stepRequested(1)
    Keys.onUpPressed: stepRequested(-1)

    TapHandler {
        acceptedButtons: Qt.MiddleButton
        onTapped: root.openRequested(true)
    }

    contentItem: RowLayout {
        spacing: Kirigami.Units.smallSpacing

        Kirigami.Icon {
            visible: root.modelData.isFolder
            source: root.modelData.iconName
            Layout.preferredWidth: Kirigami.Units.iconSizes.small
            Layout.preferredHeight: Kirigami.Units.iconSizes.small
        }

        SiteIcon {
            visible: !root.modelData.isFolder
            pageUrl: root.modelData.url
        }

        Label {
            text: root.modelData.title
            elide: Text.ElideRight
            Layout.fillWidth: true
        }

        Label {
            visible: root.modelData.isFolder
            text: root.modelData.count
            color: Kirigami.Theme.disabledTextColor
        }

        Kirigami.Icon {
            visible: root.modelData.isFolder
            source: root.isRightToLeft ? "go-previous-symbolic" : "go-next-symbolic"
            Layout.preferredWidth: Kirigami.Units.iconSizes.small
            Layout.preferredHeight: Kirigami.Units.iconSizes.small
        }
    }
}
