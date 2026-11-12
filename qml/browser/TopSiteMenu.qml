import QtQuick
import QtQuick.Controls

Menu {
    id: root

    property var site: null

    signal openRequested(string url, bool isPrivate)
    signal hideRequested(string host)

    function popupFor(request) {
        root.site = request.site
        root.popup(request.tile, request.x, request.y)
    }

    MenuItem {
        text: qsTr("Open in New Tab")
        icon.name: "tab-new"
        onTriggered: if (root.site) root.openRequested(root.site.url, false)
    }
    MenuItem {
        text: qsTr("Open in New Private Tab")
        icon.name: "view-private"
        onTriggered: if (root.site) root.openRequested(root.site.url, true)
    }
    MenuSeparator {}
    MenuItem {
        text: qsTr("Remove from Top Sites")
        icon.name: "list-remove"
        onTriggered: if (root.site) root.hideRequested(root.site.host)
    }
}
