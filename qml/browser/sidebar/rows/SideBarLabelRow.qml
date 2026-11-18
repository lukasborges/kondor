import QtQuick
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: row

    required property var group
    required property int index
    required property TabModel tabModel
    required property var targetWindow
    required property ListView list
    property bool isIconOnly: false

    width: ListView.view.width
    height: Kirigami.Units.gridUnit * 1.8
    z: header.isDragging ? 10 : 0

    SideBarGroupHeader {
        id: header
        anchors.fill: parent
        isIconOnly: row.isIconOnly
        group: row.group
        tabModel: row.tabModel
        targetWindow: row.targetWindow
        onDragStarted: row.list.groupDrag.begin(row.group)
        onDragShifted: shift => row.list.groupDrag.shift = shift
        onDropped: shift => row.drop(shift)
    }

    function drop(shift) {
        list.groupDrag.end()
        list.moveGroupBy(group, shift)
    }
}
