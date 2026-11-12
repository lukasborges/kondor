import QtQuick

WheelHandler {
    id: wheel

    required property var tabStrip

    acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
    onWheel: function(event) { wheel.scrollWith(event) }

    function scrollWith(event) {
        if (tabStrip.maxScroll > 0)
            tabStrip.scroller.jumpBy(horizontalDelta(event))
    }

    function horizontalDelta(event) {
        if (event.pixelDelta.x !== 0)
            return event.pixelDelta.x
        if (event.pixelDelta.y !== 0)
            return -event.pixelDelta.y
        if (event.angleDelta.x !== 0)
            return event.angleDelta.x
        return -event.angleDelta.y
    }
}
