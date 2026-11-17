import QtQuick
import QtQuick.Controls
import Kondor

QtObject {
    id: root

    required property var targetWindow
    required property var panes
    required property bool isPointerAtEdge
    required property bool isWindowFullScreen
    required property bool isPageFullScreen

    property bool isRevealed: false

    readonly property bool areHidden: isWindowFullScreen || Settings.hideToolbars
    readonly property bool areShown: !areHidden || isRevealed
    readonly property bool isPointerActive: isPointerAtEdge || panes.some(pane => pane.isHovered)

    signal hiddenHintRequested
    signal hiddenHintCancelled

    function reveal() {
        if (areHidden)
            isRevealed = true
    }

    function hasFocusInside() {
        return panes.some(pane => pane.containsActiveFocus())
    }

    function hasPopupOpen() {
        const overlay = targetWindow.contentItem.Overlay.overlay
        const popups = overlay ? overlay.children : []
        return Array.from(popups).some(popup => popup.visible)
    }

    function canHide() {
        return !isPointerActive && !hasFocusInside() && !hasPopupOpen()
    }

    function hideIfIdle() {
        if (canHide())
            isRevealed = false
    }

    function requestHint() {
        isRevealed = false
        if (!isPageFullScreen)
            hiddenHintRequested()
    }

    onAreHiddenChanged: {
        isRevealed = false
        if (areHidden)
            requestHint()
        else
            hiddenHintCancelled()
    }

    onIsWindowFullScreenChanged: if (isWindowFullScreen) requestHint()

    property Timer revealTimer: Timer {
        interval: 300
        running: root.areHidden && root.isPointerAtEdge && !root.isRevealed
        onTriggered: root.isRevealed = true
    }

    property Timer hideTimer: Timer {
        interval: 500
        repeat: true
        running: root.areHidden && root.isRevealed && !root.isPointerActive
        onTriggered: root.hideIfIdle()
    }
}
