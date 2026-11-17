import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

InlineBar {
    id: root

    property Tab tab: null
    readonly property TabIdentity identity: tab ? tab.identity : null

    visible: identity !== null && identity.isReloadPending

    Kirigami.Icon {
        source: "preferences-web-browser-identification"
        Layout.preferredWidth: Kirigami.Units.iconSizes.small
        Layout.preferredHeight: Kirigami.Units.iconSizes.small
    }

    Label {
        Layout.fillWidth: true
        elide: Text.ElideRight
        text: qsTr("Reload the page to use the new browser identity.")
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
        onClicked: root.identity.dismiss()
    }
}
