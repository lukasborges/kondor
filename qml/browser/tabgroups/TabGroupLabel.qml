import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Rectangle {
    id: label

    required property QtObject group
    required property TabModel tabModel
    required property var targetWindow

    property real dragShift: 0
    readonly property int tabCount: tabModel.groupRevision >= 0 ? tabModel.tabCountOf(group) : 0
    readonly property string displayName: group.name.length > 0 ? group.name : qsTr("Unnamed group")

    signal dropped(real sceneX)

    radius: Kirigami.Units.cornerRadius
    color: Qt.alpha(tint.value, hover.hovered ? 0.4 : 0.25)
    border.width: activeFocus ? 2 : 1
    border.color: activeFocus ? Kirigami.Theme.focusColor : tint.value
    activeFocusOnTab: true
    z: dragHandler.active ? 10 : 3
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

    GroupColor {
        id: tint
        name: label.group.color
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.smallSpacing
        spacing: Kirigami.Units.smallSpacing

        Rectangle {
            visible: label.group.name.length === 0
            Layout.alignment: Qt.AlignCenter
            Layout.preferredWidth: 12
            Layout.preferredHeight: 12
            radius: 6
            color: tint.value
        }

        Label {
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
        onTranslationChanged: label.dragShift = translation.x
        onActiveChanged: {
            if (!active) {
                label.dropped(centroid.scenePosition.x)
                label.dragShift = 0
            }
        }
    }

    Keys.onMenuPressed: openEditor()
    Keys.onReturnPressed: toggleCollapsed()
    Keys.onSpacePressed: toggleCollapsed()
}
