import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import Kondor

ToolButton {
    id: root

    required property TabModel tabs
    required property Item addressField

    readonly property Tab tab: tabs.currentTab
    readonly property string securityState: tab ? tab.securityState : ""
    readonly property bool isNotSecure: securityState === "insecure" || securityState === "error"
    readonly property var iconNames: ({
        "secure": "security-high",
        "insecure": "security-medium",
        "error": "security-low"
    })

    function securityIconForState(state) {
        return iconNames[state] || "text-html"
    }

    visible: tab !== null && !tab.newTabPage && tab.url.toString().length > 0
    display: text.length > 0 ? AbstractButton.TextBesideIcon : AbstractButton.IconOnly
    text: isNotSecure && !addressField.activeFocus ? qsTr("Not Secure") : ""
    icon.name: securityIconForState(securityState)
    icon.color: isNotSecure ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.textColor
    flat: true
    implicitHeight: 28
    ToolTip.visible: hovered
    ToolTip.text: qsTr("Site Information")
    ToolTip.delay: 600
    onClicked: siteInfoPopup.opened ? siteInfoPopup.close() : siteInfoPopup.open()

    SiteInfoPopup {
        id: siteInfoPopup
        parent: root.addressField
        tab: root.tab
        x: 0
        y: root.addressField.height
    }
}
