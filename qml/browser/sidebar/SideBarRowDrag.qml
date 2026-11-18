import QtQuick

DragHandler {
    id: drag

    required property Item row
    required property var tabModel

    property real shift: 0

    target: null
    xAxis.enabled: false
    yAxis.enabled: true

    function slotHeight() {
        return row.height + row.ListView.view.spacing
    }

    function limitedShift(rawShift) {
        const lowest = tabModel.clampedMoveTarget(row.index, tabModel.pinnedCount)
        const highest = tabModel.clampedMoveTarget(row.index, tabModel.count - 1)
        const low = (lowest - row.index) * slotHeight()
        const high = (highest - row.index) * slotHeight()
        return Math.max(low, Math.min(high, rawShift))
    }

    function targetIndex() {
        const slots = Math.round(shift / slotHeight())
        const lowest = tabModel.pinnedCount
        const wanted = Math.max(lowest, Math.min(row.index + slots, tabModel.count - 1))
        return tabModel.clampedMoveTarget(row.index, wanted)
    }

    function finish() {
        const target = targetIndex()
        shift = 0
        if (target !== row.index)
            tabModel.moveTab(row.index, target)
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
