import QtQuick
import Kondor

ReloadOfferBar {
    readonly property TabIdentity identity: tab ? tab.identity : null

    visible: identity !== null && identity.isReloadPending
    iconName: "preferences-web-browser-identification"
    text: qsTr("Reload the page to use the new browser identity.")
    onDismissed: identity.dismiss()
}
