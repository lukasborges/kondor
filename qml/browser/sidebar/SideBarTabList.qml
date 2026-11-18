import QtQuick
import QtQuick.Controls
import Kondor

ListView {
    id: list

    required property TabModel tabModel
    required property var targetWindow
    property bool collapsed: false

    property bool isFocusedByPointer: false
    readonly property bool isFocusRingVisible: activeFocus && !isFocusedByPointer

    readonly property alias stripModel: stripModel
    readonly property alias groupDrag: groupDrag

    signal newTabRequested()

    model: stripModel
    cacheBuffer: 100000
    clip: true
    spacing: 2
    interactive: false
    activeFocusOnTab: true
    highlight: null

    function focusWithPointer() {
        forceActiveFocus()
        isFocusedByPointer = true
    }

    function scrollBy(delta) {
        const lowest = originY
        const highest = Math.max(lowest, originY + contentHeight - height)
        contentY = Math.max(lowest, Math.min(highest, contentY + delta))
    }

    function useKeyboard() {
        isFocusedByPointer = false
    }

    function moveFocus(delta) {
        useKeyboard()
        currentIndex = nextNavigableRow(currentIndex, delta)
    }

    function isNavigableRow(row) {
        if (row < tabModel.pinnedCount || row >= stripModel.count)
            return false
        return !stripModel.isLabel(row) && !stripModel.isHidden(row)
    }

    function nextNavigableRow(from, delta) {
        let target = from + delta
        while (target >= 0 && target < stripModel.count && !isNavigableRow(target))
            target += delta
        return isNavigableRow(target) ? target : from
    }

    function currentRow() {
        return stripModel.rowOfTabIndex(tabModel.currentIndex)
    }

    function showCurrentTab() {
        currentIndex = currentRow()
        positionViewAtIndex(currentIndex, ListView.Contain)
    }

    function activateKeyboardRow() {
        useKeyboard()
        tabModel.setCurrentIndex(stripModel.tabIndexAt(currentIndex))
    }

    function isOtherTabAbove(row, group, top) {
        const item = itemAtIndex(row)
        if (!item || stripModel.isLabel(row) || stripModel.groupAt(row) === group)
            return false
        return item.y + item.height / 2 < top
    }

    function otherTabsAbove(group, top) {
        let count = 0
        for (let row = 0; row < stripModel.count; ++row)
            count += isOtherTabAbove(row, group, top) ? 1 : 0
        return count
    }

    function moveGroupBy(group, shift) {
        const header = itemAtIndex(stripModel.rowOfLabel(group))
        tabModel.moveGroup(group, otherTabsAbove(group, header.y + shift))
    }

    function isBelowRows(y) {
        return y > contentHeight - contentY
    }

    onActiveFocusChanged: isFocusedByPointer = false
    Keys.onUpPressed: moveFocus(-1)
    Keys.onDownPressed: moveFocus(1)
    Keys.onReturnPressed: activateKeyboardRow()
    Keys.onEnterPressed: activateKeyboardRow()
    Keys.onDeletePressed: { useKeyboard(); targetWindow.closeTabAt(stripModel.tabIndexAt(currentIndex)) }
    Component.onCompleted: Qt.callLater(showCurrentTab)
    onHeightChanged: Qt.callLater(showCurrentTab)
    onCountChanged: Qt.callLater(showCurrentTab)

    Connections {
        target: list.tabModel
        function onCurrentIndexChanged() { Qt.callLater(list.showCurrentTab) }
    }

    TabStripModel { id: stripModel; source: list.tabModel }
    TabGroupDragState { id: groupDrag }

    delegate: collapsed ? collapsedRows : expandedRows

    SideBarDelegateChooser { id: expandedRows; list: list }
    SideBarDelegateChooser { id: collapsedRows; list: list; isIconOnly: true }

    footer: ItemDelegate {
        width: ListView.view.width
        display: list.collapsed ? AbstractButton.IconOnly : AbstractButton.TextBesideIcon
        icon.name: "tab-new"
        text: qsTr("New Tab")
        focusPolicy: Qt.NoFocus
        ToolTip.visible: list.collapsed && hovered
        ToolTip.text: text
        ToolTip.delay: 600
        Accessible.name: text
        onClicked: list.newTabRequested()
    }

    ScrollBar.vertical: ScrollBar { policy: list.collapsed ? ScrollBar.AlwaysOff : ScrollBar.AsNeeded }

    WheelHandler {
        onWheel: event => list.scrollBy(-event.angleDelta.y / 2)
    }

    TapHandler {
        acceptedButtons: Qt.LeftButton
        onDoubleTapped: eventPoint => {
            if (list.isBelowRows(eventPoint.position.y))
                list.newTabRequested()
        }
    }
}
