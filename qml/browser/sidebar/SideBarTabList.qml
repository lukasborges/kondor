import QtQuick
import QtQuick.Controls
import Kondor

ListView {
    id: list

    required property TabModel tabModel
    required property var targetWindow

    signal newTabRequested()

    model: tabModel
    clip: true
    spacing: 2
    interactive: false
    activeFocusOnTab: true
    highlight: null

    function scrollBy(delta) {
        const lowest = originY
        const highest = Math.max(lowest, originY + contentHeight - height)
        contentY = Math.max(lowest, Math.min(highest, contentY + delta))
    }

    function moveFocus(delta) {
        const target = currentIndex + delta
        currentIndex = Math.max(tabModel.pinnedCount, Math.min(target, tabModel.count - 1))
    }

    function showCurrentTab() {
        currentIndex = tabModel.currentIndex
        positionViewAtIndex(currentIndex, ListView.Contain)
    }

    function isBelowRows(y) {
        return y > contentHeight - contentY
    }

    Keys.onUpPressed: moveFocus(-1)
    Keys.onDownPressed: moveFocus(1)
    Keys.onReturnPressed: tabModel.setCurrentIndex(currentIndex)
    Keys.onEnterPressed: tabModel.setCurrentIndex(currentIndex)
    Keys.onDeletePressed: targetWindow.closeTabAt(currentIndex)
    Component.onCompleted: Qt.callLater(showCurrentTab)
    onHeightChanged: Qt.callLater(showCurrentTab)
    onCountChanged: Qt.callLater(showCurrentTab)

    Connections {
        target: list.tabModel
        function onCurrentIndexChanged() { Qt.callLater(list.showCurrentTab) }
    }

    delegate: SideBarTabRow {
        tabModel: list.tabModel
        targetWindow: list.targetWindow
        list: ListView.view
    }

    footer: ItemDelegate {
        width: ListView.view.width
        icon.name: "tab-new"
        text: qsTr("New Tab")
        focusPolicy: Qt.NoFocus
        onClicked: list.newTabRequested()
    }

    ScrollBar.vertical: ScrollBar {}

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
