import QtQuick
import QtQuick.Controls
import Kondor

ToolButton {
    id: button

    required property Tab tab
    required property int index
    required property TabModel tabModel
    required property var targetWindow

    readonly property bool isCurrent: index === tabModel.currentIndex

    checkable: true
    checked: isCurrent
    focusPolicy: Qt.NoFocus
    Accessible.name: info.title
    ToolTip.visible: hovered
    ToolTip.text: info.title
    ToolTip.delay: 600
    onClicked: tabModel.setCurrentIndex(index)
    onToggled: checked = Qt.binding(() => isCurrent)

    TabInfo {
        id: info
        tab: button.tab
    }

    contentItem: TabIcon { tab: button.tab }

    TapHandler {
        acceptedButtons: Qt.MiddleButton
        onTapped: button.targetWindow.closeTabFor(button.tab)
    }

    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: eventPoint => button.targetWindow.openTabContextMenu(button.tab, eventPoint.scenePosition)
    }
}
