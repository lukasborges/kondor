import QtQuick
import Kondor

QtObject {
    required property Tab tab

    readonly property string title: tab?.newTabPage
        ? (tab.isPrivate ? qsTr("New Private Tab") : qsTr("New Tab"))
        : (tab?.title.length ? tab.title : qsTr("New Tab"))
    readonly property bool isSleeping: tab?.sleep.sleeping ?? false
    readonly property bool isMuted: tab?.audio.isMuted ?? false
    readonly property bool hasSoundState: isMuted || (tab?.audio.isAudible ?? false)
    readonly property string soundDescription: isMuted ? qsTr("muted") : hasSoundState ? qsTr("playing sound") : ""
    readonly property string iconOnlyName: soundDescription.length ? title + ", " + soundDescription : title
    readonly property string stateDescription: isSleeping ? qsTr("Sleeping") : ""
    readonly property string iconSource: {
        if (!tab)
            return "text-html"
        if (tab.crashed)
            return "dialog-error"
        if (tab.isPrivate)
            return "view-private"
        if (tab.newTabPage)
            return "go-home"
        return tab.iconUrl.toString().length ? tab.iconUrl.toString() : "text-html"
    }
}
