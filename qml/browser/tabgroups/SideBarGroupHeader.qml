import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "groupcolors.js" as GroupColors
import Kondor

Item {
    id: header

    required property QtObject group
    required property TabModel tabModel
    required property var targetWindow
    property bool isIconOnly: false

    readonly property string displayName: group.name.length > 0 ? group.name : qsTr("Unnamed group")
    readonly property int tabCount: tabModel.groupRevision >= 0 ? tabModel.tabCountOf(group) : 0

    Accessible.role: Accessible.Button
    Accessible.name: displayName
    Accessible.description: group.collapsed ? qsTr("Collapsed") : ""

    Rectangle {
        anchors.fill: parent
        radius: Kirigami.Units.cornerRadius
        color: Qt.alpha(GroupColors.of(header.group.color, Kirigami.Theme), 0.2)
        visible: headerMouse.containsMouse
    }


    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Kirigami.Units.smallSpacing * 2
        anchors.rightMargin: Kirigami.Units.smallSpacing
        spacing: Kirigami.Units.smallSpacing

        Item { visible: header.isIconOnly; Layout.fillWidth: true }

        Rectangle {
            Layout.preferredWidth: 10
            Layout.preferredHeight: 10
            radius: 5
            color: GroupColors.of(header.group.color, Kirigami.Theme)
        }

        Label {
            visible: !header.isIconOnly
            Layout.fillWidth: true
            text: header.group.name
            font.bold: true
            elide: Text.ElideRight
        }

        Label {
            visible: !header.isIconOnly && header.group.collapsed
            text: header.tabCount
            color: Kirigami.Theme.disabledTextColor
        }

        Kirigami.Icon {
            visible: !header.isIconOnly
            source: header.group.collapsed ? "arrow-right" : "arrow-down"
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
        }

        Item { visible: header.isIconOnly; Layout.fillWidth: true }
    }

    MouseArea {
        id: headerMouse
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        hoverEnabled: true
        ToolTip.visible: containsMouse
        ToolTip.text: header.displayName
        ToolTip.delay: 600
        onClicked: mouse => {
            if (mouse.button === Qt.RightButton)
                header.targetWindow.openGroupEditor(header.group, header)
            else
                header.tabModel.setGroupCollapsed(header.group, !header.group.collapsed)
        }
    }
}
