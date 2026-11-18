import QtQuick
import Kondor

TabSearchPopup {
    id: root

    required property var headerButton
    required property var sideBarButton
    required property bool tabsInSideBar

    function show() {
        if (tabsInSideBar)
            openFor(sideBarButton, true)
        else
            openFor(headerButton, false)
    }

    Binding {
        target: root.headerButton
        property: "checked"
        value: root.opened && !root.tabsInSideBar
    }

    Binding {
        target: root.sideBarButton
        property: "checked"
        value: root.opened && root.tabsInSideBar
    }
}
