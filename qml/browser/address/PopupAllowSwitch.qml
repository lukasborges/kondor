import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kondor

RowLayout {
    id: root

    property TabPopups popups: null

    visible: popups !== null && popups.canChangeAllowed && popups.host.length > 0

    Switch {
        id: allowSwitch
        Accessible.name: label.text
        onToggled: root.popups.setAllowed(checked)
    }

    Binding {
        target: allowSwitch
        property: "checked"
        value: root.popups !== null && root.popups.isAllowed
    }

    Label {
        id: label
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: root.popups ? qsTr("Allow pop-ups from %1").arg(root.popups.host) : ""

        TapHandler {
            gesturePolicy: TapHandler.ReleaseWithinBounds
            onTapped: root.popups.setAllowed(!root.popups.isAllowed)
        }
    }
}
