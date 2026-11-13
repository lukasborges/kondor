import QtQuick
import QtQuick.Controls
import Kondor

ToolButton {
    id: root

    required property TabModel tabs

    visible: tabs.currentTab
             ? (tabs.currentTab.readerAvailable || tabs.currentTab.readerActive)
             : false
    display: AbstractButton.IconOnly
    icon.name: "view-readermode"
    icon.width: 16
    icon.height: 16
    flat: true
    checked: tabs.currentTab ? tabs.currentTab.readerActive : false
    implicitWidth: 28
    implicitHeight: 28
    ToolTip.visible: hovered
    Accessible.name: ToolTip.text
    ToolTip.text: checked ? qsTr("Exit Reader Mode (Ctrl+Alt+R)") : qsTr("Reader Mode (Ctrl+Alt+R)")
    ToolTip.delay: 600
    onClicked: tabs.currentTab.toggleReaderMode()
}
