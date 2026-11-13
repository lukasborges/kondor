import QtQuick
import QtQuick.Controls
import QtQuick.Window
import Kondor

QtObject {
    id: root

    required property ApplicationWindow targetWindow
    required property TabModel tabs
    required property var hint

    property bool pageFullScreen: tabs.currentTab ? tabs.currentTab.isFullScreen : false
    property bool windowFullScreen: false
    property int visibilityBeforeFullScreen: Window.Windowed

    function updateFullScreen() {
        if (pageFullScreen || windowFullScreen)
            enterFullScreen()
        else
            leaveFullScreen()
    }

    function enterFullScreen() {
        if (targetWindow.visibility !== Window.FullScreen)
            visibilityBeforeFullScreen = targetWindow.visibility
        targetWindow.showFullScreen()
    }

    function leaveFullScreen() {
        if (visibilityBeforeFullScreen === Window.Maximized)
            targetWindow.showMaximized()
        else
            targetWindow.showNormal()
    }

    function showOrHideHint() {
        if (pageFullScreen)
            hint.show()
        else
            hint.hide()
    }

    onPageFullScreenChanged: {
        showOrHideHint()
        updateFullScreen()
    }

    onWindowFullScreenChanged: updateFullScreen()
}
