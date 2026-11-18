import QtQuick
import QtQuick.Controls
import Kondor

TabButton {
    id: item

    required property var group
    required property int index
    required property var tabStrip

    readonly property alias label: label

    width: tabStrip.layout.rowWidth(index)
    checkable: false
    focusPolicy: Qt.NoFocus
    hoverEnabled: false
    padding: 0
    background: null
    contentItem: Item {}
    z: label.isDragging ? 10 : 3

    TabGroupLabel {
        id: label
        y: 2
        width: item.width - 2
        height: item.height - 4
        group: item.group
        tabModel: item.tabStrip.tabModel
        targetWindow: item.tabStrip.targetWindow
        onDragStarted: item.tabStrip.groupDrag.begin(item.group)
        onDragShifted: shift => item.tabStrip.groupDrag.shift = shift
        onDropped: shift => item.drop(shift)
    }

    function drop(shift) {
        tabStrip.groupDrag.end()
        tabStrip.layout.moveGroupBy(group, shift)
    }
}
