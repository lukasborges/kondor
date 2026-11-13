import QtQuick

DragHandler {
    id: drag

    required property Item tabButton
    required property var slide

    readonly property var tabStrip: tabButton.tabStrip
    readonly property var tabModel: tabButton.tabModel
    readonly property bool isAutoScrolling: active && tabStrip && tabStrip.maxScroll > 0
    property real sceneX: 0
    property real sceneY: 0
    property real grabOffset: 0

    target: null
    xAxis.enabled: true
    yAxis.enabled: false

    function contentX(sceneX, sceneY) {
        return tabButton.parent.mapFromItem(null, sceneX, sceneY).x
    }

    function clamp(value, low, high) {
        return Math.max(low, Math.min(high, value))
    }

    function sectionRange() {
        const pinnedEnd = tabStrip.scroller.tabX(tabButton.pinnedCount)
        if (tabButton.tab.pinned)
            return { start: 0, end: pinnedEnd }
        return { start: pinnedEnd, end: tabStrip.scroller.stripWidth }
    }

    function clampedLeft() {
        const range = sectionRange()
        const left = contentX(sceneX, sceneY) - tabStrip.scroller.origin - grabOffset
        return clamp(left, range.start, range.end - tabButton.width)
    }

    function targetIndex(center) {
        const pinnedCount = tabButton.pinnedCount
        if (tabButton.tab.pinned)
            return clamp(Math.floor(center / tabStrip.pinnedTabWidth), 0, pinnedCount - 1)
        const slot = Math.floor((center - tabStrip.scroller.tabX(pinnedCount)) / tabStrip.tabWidth)
        return clamp(pinnedCount + slot, pinnedCount, tabModel.count - 1)
    }

    function reorderTo(left) {
        const own = tabModel.indexOfTab(tabButton.tab)
        const target = targetIndex(left + tabButton.width / 2)
        if (target === own)
            return
        tabModel.moveTab(own, target)
        tabButton.tabBarItem.contentItem.forceLayout()
    }

    function update() {
        if (!tabStrip || !tabButton.parent)
            return
        const left = clampedLeft()
        reorderTo(left)
        tabButton.dragShift = left + tabStrip.scroller.origin - tabButton.x
    }

    function edgeScrollDelta() {
        const view = tabStrip.scroller.view
        const x = view.mapFromItem(null, sceneX, sceneY).x
        if (x < 24)
            return -8
        return x > view.width - 24 ? 8 : 0
    }

    function autoScroll() {
        const delta = edgeScrollDelta()
        if (delta === 0)
            return
        tabStrip.scroller.jumpBy(delta)
        update()
    }

    function recordPointer(scenePosition) {
        sceneX = scenePosition.x
        sceneY = scenePosition.y
    }

    function beginDrag() {
        recordPointer(centroid.scenePosition)
        grabOffset = contentX(centroid.scenePressPosition.x, centroid.scenePressPosition.y) - tabButton.x
        tabModel.setCurrentIndex(tabModel.indexOfTab(tabButton.tab))
        slide.stopSettling()
        update()
    }

    function endDrag() {
        slide.startSettling()
        if (tabStrip)
            tabStrip.scroller.scheduleEnsureVisible()
    }

    function abortOnDestruction() {
        if (!active || !tabStrip)
            return
        tabStrip.tabDragActive = false
        tabStrip.scroller.scheduleEnsureVisible()
    }

    onCentroidChanged: {
        if (!active)
            return
        recordPointer(centroid.scenePosition)
        update()
    }

    onActiveChanged: {
        if (tabStrip)
            tabStrip.tabDragActive = active
        if (active)
            beginDrag()
        else
            endDrag()
    }
}
