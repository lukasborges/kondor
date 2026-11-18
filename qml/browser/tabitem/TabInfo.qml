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
    readonly property bool isAgentTab: RemoteControl.active && (tab?.agent.hasAccess ?? false)
    readonly property string agentDescription: {
        if (!isAgentTab)
            return ""
        if (tab.agent.workingName.length)
            return qsTr("%1 is working in this tab").arg(tab.agent.workingName)
        if (tab.agent.name.length)
            return qsTr("Opened by %1").arg(tab.agent.name)
        return qsTr("Agents can use this tab")
    }
    readonly property string stateDescription: [isSleeping ? qsTr("Sleeping") : "", agentDescription]
        .filter(text => text.length).join(", ")
    readonly property string providerPrefix: "image://favicon/"
    readonly property string pageIconUrl: tab?.iconUrl.toString() ?? ""
    readonly property bool hasPageIcon: !isNamedIcon && pageIconUrl.startsWith(providerPrefix)
    readonly property string pageIconSource: hasPageIcon
        ? "image://kondor-tabicon/" + pageIconUrl.substring(providerPrefix.length)
        : ""
    readonly property bool isNamedIcon: !tab || tab.crashed || tab.isPrivate || tab.newTabPage
    readonly property string iconSource: {
        if (!tab)
            return "text-html"
        if (tab.crashed)
            return "dialog-error"
        if (tab.isPrivate)
            return "view-private"
        if (tab.newTabPage)
            return "go-home"
        return "text-html"
    }
}
