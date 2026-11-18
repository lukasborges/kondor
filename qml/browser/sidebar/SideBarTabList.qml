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

    signal newTabRequested()

    model: tabModel
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
        currentIndex = nextShownIndex(currentIndex, delta)
    }

    function nextShownIndex(from, delta) {
        const lowest = tabModel.pinnedCount
        let target = Math.max(lowest, Math.min(from + delta, tabModel.count - 1))
        while (tabModel.isHiddenByGroup(target) && target > lowest && target < tabModel.count - 1)
            target += delta
        return target
    }

    function showCurrentTab() {
        currentIndex = tabModel.currentIndex
        positionViewAtIndex(currentIndex, ListView.Contain)
    }

    function activateKeyboardRow() {
        useKeyboard()
        tabModel.setCurrentIndex(currentIndex)
    }

    function isBelowRows(y) {
        return y > contentHeight - contentY
    }

    onActiveFocusChanged: isFocusedByPointer = false
    Keys.onUpPressed: moveFocus(-1)
    Keys.onDownPressed: moveFocus(1)
    Keys.onReturnPressed: activateKeyboardRow()
    Keys.onEnterPressed: activateKeyboardRow()
    Keys.onDeletePressed: { useKeyboard(); targetWindow.closeTabAt(currentIndex) }
    Component.onCompleted: Qt.callLater(showCurrentTab)
    onHeightChanged: Qt.callLater(showCurrentTab)
    onCountChanged: Qt.callLater(showCurrentTab)

    Connections {
        target: list.tabModel
        function onCurrentIndexChanged() { Qt.callLater(list.showCurrentTab) }
    }

    delegate: collapsed ? collapsedRow : expandedRow

    Component {
        id: expandedRow

        SideBarTabRow {
            tabModel: list.tabModel
            targetWindow: list.targetWindow
            list: ListView.view
        }
    }

    Component {
        id: collapsedRow

        SideBarCollapsedTabRow {
            tabModel: list.tabModel
            targetWindow: list.targetWindow
            list: ListView.view
        }
    }

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
