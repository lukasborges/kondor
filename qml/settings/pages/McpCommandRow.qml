import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kondor

RowLayout {
    TextField {
        readOnly: true
        font.family: "monospace"
        text: RemoteControl.mcpCommand
        Layout.fillWidth: true
        ToolTip.visible: hovered
        ToolTip.text: text
        ToolTip.delay: 600
        Accessible.name: qsTr("MCP server command")
    }

    CopyFeedbackButton {
        iconName: "edit-copy"
        tooltipText: qsTr("Copy Command")
        copiedTooltipText: qsTr("Copied")
        announcement: qsTr("Command copied")
        accessibleName: qsTr("Copy Command")
        onCopyRequested: RemoteControl.copyMcpCommand()
    }
}
