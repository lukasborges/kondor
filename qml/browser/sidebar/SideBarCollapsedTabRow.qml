import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import Kondor

ToolButton {
    id: row

    required property Tab tab
    required property int index
    required property TabModel tabModel
    required property var targetWindow
    required property ListView list

    readonly property bool isCurrent: index === tabModel.currentIndex
    readonly property bool hasKeyboardFocus: list.isFocusRingVisible && index === list.currentIndex

    visible: !tab.pinned
    height: tab.pinned ? 0 : implicitHeight
    x: (ListView.view.width - width) / 2
    z: drag.active ? 10 : 0
    checkable: true
    checked: isCurrent
    focusPolicy: Qt.NoFocus
    Accessible.name: info.title
    ToolTip.visible: hovered
    ToolTip.text: info.title
    ToolTip.delay: 600
    transform: Translate { y: drag.shift }
    onToggled: checked = Qt.binding(() => row.isCurrent)
    onClicked: {
        tabModel.setCurrentIndex(index)
        list.focusWithPointer()
    }

    TabInfo {
        id: info
        tab: row.tab
    }

    contentItem: TabIcon { tab: row.tab }

    SideBarFocusRing {
        anchors.fill: parent
        visible: row.hasKeyboardFocus
        radius: Kirigami.Units.cornerRadius
    }

    TapHandler {
        acceptedButtons: Qt.MiddleButton
        onTapped: row.targetWindow.closeTabFor(row.tab)
    }

    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: eventPoint => row.targetWindow.openTabContextMenu(row.tab, eventPoint.scenePosition)
    }

    SideBarRowDrag {
        id: drag
        row: row
        tabModel: row.tabModel
    }
}
