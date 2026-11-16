import QtQuick
import Kondor

QtObject {
    id: root

    required property var tab
    required property bool isPrivateWindow

    readonly property string text: titleParts().join(" — ")

    function titleParts() {
        const parts = [pageTitle()]
        if (isPrivateWindow)
            parts.push(qsTr("Private Browsing"))
        parts.push(Qt.application.displayName)
        return parts.filter(part => part.length > 0)
    }

    function pageTitle() {
        if (!tab)
            return ""
        return tab.newTabPage ? newTabTitle() : tab.title
    }

    function newTabTitle() {
        return tab.isPrivate ? qsTr("New Private Tab") : qsTr("New Tab")
    }
}
