import QtQuick
import Kondor

TabSearchPopup {
    required property var headerButton
    required property var sideBarButton

    function show() {
        if (Settings.tabStyle === "vertical")
            openFor(sideBarButton, true)
        else
            openFor(headerButton, false)
    }
}
