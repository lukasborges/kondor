import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

InlineBar {
    id: root

    property Tab tab: null
    readonly property TabSiteReload siteReload: tab ? tab.siteReload : null

    visible: siteReload !== null && siteReload.isPending

    Kirigami.Icon {
        source: "preferences-plugin"
        Layout.preferredWidth: Kirigami.Units.iconSizes.small
        Layout.preferredHeight: Kirigami.Units.iconSizes.small
    }

    Label {
        Layout.fillWidth: true
        elide: Text.ElideRight
        text: !root.siteReload ? ""
              : root.siteReload.willRun
                ? qsTr("%1 will run on this site after reloading.").arg(root.siteReload.extensionName)
                : qsTr("%1 will stop running on this site after reloading.").arg(root.siteReload.extensionName)
    }

    Button {
        text: qsTr("Reload")
        icon.name: "view-refresh"
        onClicked: root.tab.reload()
    }

    ToolButton {
        display: AbstractButton.IconOnly
        icon.name: "window-close"
        text: qsTr("Close")
        Accessible.name: text
        ToolTip.visible: hovered
        ToolTip.text: text
        ToolTip.delay: 600
        onClicked: root.siteReload.dismiss()
    }
}
