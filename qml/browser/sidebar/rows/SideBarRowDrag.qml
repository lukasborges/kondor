import QtQuick

DragHandler {
    id: drag

    required property Item row
    required property var tabModel

    readonly property var list: row.ListView.view
    property real shift: 0

    target: null
    xAxis.enabled: false
    yAxis.enabled: true

    function yOfTab(tabIndex) {
        const item = list.itemAtIndex(list.stripModel.rowOfTabIndex(tabIndex))
        return item ? item.y : row.y
    }

    function limitedShift(rawShift) {
        const lowest = tabModel.clampedMoveTarget(row.tabIndex, tabModel.pinnedCount)
        const highest = tabModel.clampedMoveTarget(row.tabIndex, tabModel.count - 1)
        return Math.max(yOfTab(lowest) - row.y, Math.min(yOfTab(highest) - row.y, rawShift))
    }

    function targetIndex() {
        const hit = list.indexAt(0, row.y + row.height / 2 + shift)
        const wanted = hit < 0 ? row.tabIndex : list.stripModel.tabIndexAt(hit)
        const clamped = Math.max(tabModel.pinnedCount, Math.min(wanted, tabModel.count - 1))
        return tabModel.clampedMoveTarget(row.tabIndex, clamped)
    }

    function finish() {
        const target = targetIndex()
        shift = 0
        if (target !== row.tabIndex)
            tabModel.moveTab(row.tabIndex, target)
    }

    onCentroidChanged: {
        if (active)
            shift = limitedShift(centroid.scenePosition.y - centroid.scenePressPosition.y)
    }

    onActiveChanged: {
        if (!active)
            finish()
    }
}
