import QtQuick
import org.kde.kirigami as Kirigami

Item {
    id: scroller

    required property var tabStrip

    readonly property Item view: tabStrip.tabBar.contentItem
    readonly property real stripWidth: tabX(tabStrip.tabModel.count)
    readonly property real viewWidth: view ? Math.min(stripWidth, view.width) : 0
    readonly property real maxScroll: Math.max(0, stripWidth - viewWidth)
    readonly property real origin: view ? view.originX : 0
    readonly property real scrolled: view ? view.contentX - view.originX : 0

    function tabX(index) {
        const pinned = tabStrip.pinnedCount
        if (index < pinned)
            return index * tabStrip.pinnedTabWidth
        return pinned * tabStrip.pinnedTabWidth + (index - pinned) * tabStrip.tabWidth
    }

    function scrollTo(x) {
        if (!view)
            return
        const clamped = view.originX + Math.max(0, Math.min(maxScroll, x))
        scrollAnimation.stop()
        if (!isAlreadyAt(clamped))
            animateTo(clamped)
    }

    function isAlreadyAt(contentX) {
        return Math.abs(contentX - view.contentX) < 0.5
    }

    function animateTo(contentX) {
        scrollAnimation.from = view.contentX
        scrollAnimation.to = contentX
        scrollAnimation.start()
    }

    function scrollTarget() {
        if (!view)
            return 0
        return (scrollAnimation.running ? scrollAnimation.to : view.contentX) - view.originX
    }

    function scrollBy(delta) {
        scrollTo(scrollTarget() + delta)
    }

    function jumpBy(delta) {
        if (!view)
            return
        scrollAnimation.stop()
        view.contentX = view.originX + Math.max(0, Math.min(maxScroll, scrolled + delta))
    }

    function positionToShowCurrent(left, right) {
        const current = scrollTarget()
        if (left < current)
            return left
        if (right > current + viewWidth)
            return right - viewWidth
        return current
    }

    function ensureCurrentVisible() {
        const index = tabStrip.tabModel.currentIndex
        if (!view || index < 0)
            return
        view.forceLayout()
        scrollTo(positionToShowCurrent(tabX(index), tabX(index + 1)))
    }

    function scheduleEnsureVisible() {
        if (!tabStrip.tabDragActive)
            Qt.callLater(ensureCurrentVisible)
    }

    NumberAnimation {
        id: scrollAnimation
        target: scroller.view
        property: "contentX"
        duration: Kirigami.Units.shortDuration
        easing.type: Easing.OutCubic
    }

    Connections {
        target: scroller.view
        function onContentWidthChanged() { scroller.scheduleEnsureVisible() }
        function onWidthChanged() { scroller.scheduleEnsureVisible() }
    }
}
