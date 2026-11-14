import QtQuick

DragHandler {
    id: drag

    required property Item row
    required property var tabModel

    property real shift: 0

    target: null
    xAxis.enabled: false
    yAxis.enabled: true

    function targetIndex() {
        const slots = Math.round(shift / row.height)
        const lowest = tabModel.pinnedCount
        return Math.max(lowest, Math.min(row.index + slots, tabModel.count - 1))
    }

    function finish() {
        const target = targetIndex()
        shift = 0
        if (target !== row.index)
            tabModel.moveTab(row.index, target)
    }

    onCentroidChanged: {
        if (active)
            shift = centroid.scenePosition.y - centroid.scenePressPosition.y
    }

    onActiveChanged: {
        if (!active)
            finish()
    }
}
