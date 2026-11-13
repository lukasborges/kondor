import QtQuick

Item {
    id: taps

    required property var tabStrip

    function emptyAt(sceneX, sceneY) {
        return !isOnButton(sceneX, sceneY) && !isOnTab(sceneX, sceneY)
    }

    function isOnButton(sceneX, sceneY) {
        const buttons = [tabStrip.newTabButton, tabStrip.scrollLeftButton, tabStrip.scrollRightButton]
        return buttons.some(button => button.visible && contains(button, sceneX, sceneY))
    }

    function contains(button, sceneX, sceneY) {
        const point = button.mapFromItem(null, sceneX, sceneY)
        return point.x >= 0 && point.x <= button.width && point.y >= 0 && point.y <= button.height
    }

    function isOnTab(sceneX, sceneY) {
        const view = tabStrip.scroller.view
        if (!view)
            return false
        const point = view.mapFromItem(null, sceneX, sceneY)
        return point.x >= 0 && point.x <= view.width
            && point.x + view.contentX <= view.originX + view.contentWidth
    }

    function requestNewTabIfEmpty(eventPoint) {
        if (emptyAt(eventPoint.scenePosition.x, eventPoint.scenePosition.y))
            tabStrip.newTabRequested()
    }

    TapHandler {
        acceptedButtons: Qt.LeftButton
        onDoubleTapped: function(eventPoint) { taps.requestNewTabIfEmpty(eventPoint) }
    }

    TapHandler {
        acceptedButtons: Qt.MiddleButton
        onTapped: function(eventPoint) { taps.requestNewTabIfEmpty(eventPoint) }
    }
}
