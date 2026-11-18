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

    readonly property bool isGroupStart: tabModel.groupRevision >= 0 && tabModel.isGroupStart(index)
    readonly property bool isHiddenByGroup: tabModel.groupRevision >= 0 && tabModel.isHiddenByGroup(index)
    readonly property real headerHeight: isGroupStart ? Kirigami.Units.gridUnit * 1.8 : 0

    visible: height > 0
    width: ListView.view.width
    height: tab.pinned ? 0 : headerHeight + (isHiddenByGroup ? 0 : button.height)
    z: drag.active ? 10 : 0
    transform: Translate { y: drag.shift }

    Loader {
        active: row.isGroupStart
        width: row.width
        height: row.headerHeight
        sourceComponent: SideBarGroupHeader {
            isIconOnly: true
            group: row.tab.group
            tabModel: row.tabModel
            targetWindow: row.targetWindow
        }
    }

    TabGroupBar {
        isVertical: true
        group: row.tab.group
        visible: group !== null && !row.isHiddenByGroup
        anchors.topMargin: row.headerHeight + Kirigami.Units.smallSpacing
    }

    SideBarTabButton {
        id: button
        y: row.headerHeight
        visible: !row.isHiddenByGroup
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
