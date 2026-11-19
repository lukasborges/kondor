import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "groupcolors.js" as GroupColors
import Kondor

Rectangle {
    id: label

    required property QtObject group
    required property TabModel tabModel
    required property var targetWindow

    readonly property alias nameLabel: nameLabel
    property real dragShift: 0
    readonly property int tabCount: tabModel.groupRevision >= 0 ? tabModel.tabCountOf(group) : 0
    readonly property string displayName: group.name.length > 0 ? group.name : qsTr("Unnamed group")

    readonly property bool isDragging: dragHandler.active

    signal dragStarted()
    signal dragShifted(real shift)
    signal dropped(real shift)

    radius: Kirigami.Units.cornerRadius
    color: Qt.alpha(GroupColors.of(label.group.color, Kirigami.Theme), hover.hovered ? 0.4 : 0.25)
    border.width: activeFocus ? 2 : 1
    border.color: activeFocus ? Kirigami.Theme.focusColor : GroupColors.of(label.group.color, Kirigami.Theme)
    activeFocusOnTab: true
    transform: Translate { x: label.dragShift }
    Accessible.role: Accessible.Button
    Accessible.name: displayName
    Accessible.description: group.collapsed ? qsTr("Collapsed") : ""
    ToolTip.visible: hover.hovered
    ToolTip.text: displayName
    ToolTip.delay: 600

    function toggleCollapsed() {
        tabModel.setGroupCollapsed(group, !group.collapsed)
    }

    function openEditor() {
        targetWindow.openGroupEditor(group, label)
    }

    function followDrag(shift) {
        if (!dragHandler.active)
            return
        dragShift = shift
        dragShifted(shift)
    }

    function endDrag() {
        const shift = dragShift
        dragShift = 0
        dropped(shift)
    }

    RowLayout {
        anchors.centerIn: parent
        width: Math.min(implicitWidth, label.width - Kirigami.Units.smallSpacing * 2)
        spacing: Kirigami.Units.smallSpacing

        Rectangle {
            visible: label.group.name.length === 0
            Layout.alignment: Qt.AlignCenter
            Layout.preferredWidth: 12
            Layout.preferredHeight: 12
            radius: 6
            color: GroupColors.of(label.group.color, Kirigami.Theme)
        }

        Label {
            id: nameLabel
            visible: label.group.name.length > 0
            Layout.fillWidth: true
            text: label.group.name
            font.bold: true
            elide: Text.ElideRight
        }

        Label {
            visible: label.group.collapsed
            Layout.alignment: Qt.AlignCenter
            text: label.tabCount
            color: Kirigami.Theme.disabledTextColor
        }
    }

    HoverHandler { id: hover }

    TapHandler {
        acceptedButtons: Qt.LeftButton
        onTapped: label.toggleCollapsed()
    }

    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: label.openEditor()
    }

    DragHandler {
        id: dragHandler
        target: null
        yAxis.enabled: false
        grabPermissions: PointerHandler.CanTakeOverFromAnything
        onTranslationChanged: label.followDrag(translation.x)
        onActiveChanged: dragHandler.active ? label.dragStarted() : label.endDrag()
    }

    Keys.onMenuPressed: openEditor()
    Keys.onReturnPressed: toggleCollapsed()
    Keys.onSpacePressed: toggleCollapsed()
}
