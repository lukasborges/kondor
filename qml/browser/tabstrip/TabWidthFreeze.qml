import QtQuick

Item {
    id: freeze

    required property var tabStrip

    property real frozenWidth: 0
    property bool closingWithMouse: false

    function closeWithMouse(tab) {
        if (shouldFreeze())
            freezeCurrentWidth()
        tabStrip.targetWindow.closeTabFor(tab)
        closingWithMouse = false
    }

    function shouldFreeze() {
        return tabStrip.tabWidth < tabStrip.standardTabWidth && tabStrip.tabModel.count > 1
    }

    function freezeCurrentWidth() {
        frozenWidth = tabStrip.tabWidth
        closingWithMouse = true
        unfreezeTimer.restart()
    }

    function unfreeze() {
        frozenWidth = 0
        unfreezeTimer.stop()
    }

    function unfreezeUnlessClosingWithMouse() {
        if (!closingWithMouse)
            unfreeze()
    }

    Timer {
        id: unfreezeTimer
        interval: 1000
        onTriggered: if (!barHover.hovered) freeze.unfreeze()
    }

    HoverHandler {
        id: barHover
        parent: freeze.tabStrip
        onHoveredChanged: if (!hovered) freeze.unfreeze()
    }
}
