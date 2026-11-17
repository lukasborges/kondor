import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

InlineBar {
    id: root

    property Tab tab: null
    property string iconName: ""
    property string text: ""

    signal dismissed()

    Kirigami.Icon {
        source: root.iconName
        Layout.preferredWidth: Kirigami.Units.iconSizes.small
        Layout.preferredHeight: Kirigami.Units.iconSizes.small
    }

    Label {
        Layout.fillWidth: true
        elide: Text.ElideRight
        text: root.text
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
        onClicked: root.dismissed()
    }
}
