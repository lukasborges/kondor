import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

InlineBar {
    id: root

    property Tab tab: null
    property var dismissedUrls: []

    readonly property string pageUrl: tab ? tab.url.toString() : ""

    visible: tab !== null && !tab.isPrivate && !tab.loading
             && ExtensionManager.isUserScriptUrl(tab.url)
             && dismissedUrls.indexOf(pageUrl) < 0

    function dismiss() {
        dismissedUrls = dismissedUrls.concat([pageUrl])
    }

    Kirigami.Icon {
        source: "text-x-javascript"
        Layout.preferredWidth: Kirigami.Units.iconSizes.small
        Layout.preferredHeight: Kirigami.Units.iconSizes.small
    }

    Label {
        Layout.fillWidth: true
        elide: Text.ElideRight
        text: qsTr("This page is a user script.")
    }

    Button {
        text: qsTr("Install…")
        icon.name: "download"
        onClicked: ExtensionManager.inspectUserScript(root.tab.url)
    }

    ToolButton {
        display: AbstractButton.IconOnly
        icon.name: "window-close"
        text: qsTr("Close")
        Accessible.name: text
        ToolTip.visible: hovered
        ToolTip.text: text
        ToolTip.delay: 600
        onClicked: root.dismiss()
    }
}
