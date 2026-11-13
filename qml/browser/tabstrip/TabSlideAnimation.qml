import QtQuick
import org.kde.kirigami as Kirigami

Item {
    id: slide

    required property Item tabButton
    required property var tabStrip
    required property var dragHandler

    readonly property bool isSettling: settleAnimation.running
    property real lastX: 0

    function startSettling() {
        settleAnimation.start()
    }

    function stopSettling() {
        settleAnimation.stop()
    }

    function followPosition() {
        if (dragHandler.active)
            dragHandler.update()
        else if (tabStrip && tabStrip.tabDragActive)
            slideToNewSlot()
        lastX = tabButton.x
    }

    function slideToNewSlot() {
        tabButton.slideShift += lastX - tabButton.x
        slideAnimation.restart()
    }

    Component.onCompleted: lastX = tabButton.x

    NumberAnimation {
        id: settleAnimation
        target: slide.tabButton
        property: "dragShift"
        to: 0
        duration: Kirigami.Units.shortDuration
        easing.type: Easing.OutCubic
    }

    NumberAnimation {
        id: slideAnimation
        target: slide.tabButton
        property: "slideShift"
        to: 0
        duration: Kirigami.Units.shortDuration
        easing.type: Easing.OutCubic
    }
}
