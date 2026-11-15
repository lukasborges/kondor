import QtQuick
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: row

    required property Tab tab
    required property int index
    required property TabModel tabModel
    required property var targetWindow
    required property ListView list

    readonly property bool hasKeyboardFocus: list.isFocusRingVisible && index === list.currentIndex

    visible: !tab.pinned
    width: ListView.view.width
    height: tab.pinned ? 0 : button.height
    z: drag.active ? 10 : 0
    transform: Translate { y: drag.shift }

    SideBarTabButton {
        id: button
        anchors.horizontalCenter: parent.horizontalCenter
        tab: row.tab
        index: row.index
        tabModel: row.tabModel
        targetWindow: row.targetWindow
        onClicked: row.list.focusWithPointer()
    }

    SideBarFocusRing {
        anchors.fill: button
        visible: row.hasKeyboardFocus
        radius: Kirigami.Units.cornerRadius
    }

    SideBarRowDrag {
        id: drag
        row: row
        tabModel: row.tabModel
    }
}
