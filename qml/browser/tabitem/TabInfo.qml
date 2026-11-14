import QtQuick
import Kondor

QtObject {
    required property Tab tab

    readonly property string title: tab.newTabPage
        ? (tab.isPrivate ? qsTr("New Private Tab") : qsTr("New Tab"))
        : (tab.title.length ? tab.title : qsTr("New Tab"))
    readonly property string iconSource: {
        if (tab.crashed)
            return "dialog-error"
        if (tab.isPrivate)
            return "view-private"
        if (tab.newTabPage)
            return "tab-new"
        return tab.iconUrl.toString().length ? tab.iconUrl.toString() : "text-html"
    }
}
