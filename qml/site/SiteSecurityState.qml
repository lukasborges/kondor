import QtQuick
import org.kde.kirigami as Kirigami
import Kondor

QtObject {
    id: root

    property Tab tab: null

    readonly property string securityState: tab ? tab.security.state : ""
    readonly property var icons: ({
        "secure": "security-high",
        "insecure": "security-medium",
        "error": "security-low"
    })
    readonly property var texts: ({
        "secure": qsTr("Connection is secure"),
        "insecure": qsTr("Not Secure"),
        "error": qsTr("Your connection is not private")
    })
    readonly property var colors: ({
        "secure": Kirigami.Theme.positiveTextColor,
        "insecure": Kirigami.Theme.negativeTextColor,
        "error": Kirigami.Theme.negativeTextColor
    })
    readonly property string stateIcon: icons[securityState] ?? "text-html"
    readonly property string stateText: texts[securityState] ?? qsTr("Local file")
    readonly property color stateColor: colors[securityState] ?? Kirigami.Theme.disabledTextColor

    function siteName() {
        if (!tab)
            return ""
        const text = tab.url.toString()
        const match = text.match(/^[a-z][a-z0-9+.-]*:\/\/([^\/?#]+)/i)
        return match ? match[1] : text
    }

    function originUrl() {
        if (!tab)
            return ""
        const match = tab.url.toString().match(/^(https?:\/\/[^\/?#]+)/i)
        return match ? match[1] : ""
    }
}
