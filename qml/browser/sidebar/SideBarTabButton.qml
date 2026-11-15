import QtQuick
import QtQuick.Controls
import Kondor

ToolButton {
    id: button

    required property Tab tab
    required property int index
    required property TabModel tabModel
    required property var targetWindow

    checked: index === tabModel.currentIndex
    focusPolicy: Qt.NoFocus
    Accessible.name: info.title
    ToolTip.visible: hovered
    ToolTip.text: info.title
    ToolTip.delay: 600
    onClicked: tabModel.setCurrentIndex(index)

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
