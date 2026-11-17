import QtQuick
import Kondor

ReloadOfferBar {
    readonly property TabSiteReload siteReload: tab ? tab.siteReload : null

    visible: siteReload !== null && siteReload.isPending
    iconName: "preferences-plugin"
    text: message()
    onDismissed: siteReload.dismiss()

    function message() {
        if (!siteReload)
            return ""
        if (siteReload.willRun)
            return qsTr("%1 will run on this site after reloading.").arg(siteReload.extensionName)
        return qsTr("%1 will stop running on this site after reloading.").arg(siteReload.extensionName)
    }
}
