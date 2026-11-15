import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ItemDelegate {
    id: row

    required property Tab tab
    required property int index
    required property TabModel tabModel
    required property var targetWindow
    required property ListView list
    property bool collapsed: false

    readonly property bool isPinned: tab?.pinned ?? false
    readonly property bool isCurrent: index === tabModel.currentIndex
    readonly property bool hasKeyboardFocus: list.isFocusRingVisible && index === list.currentIndex
    readonly property real collapsedInset: Math.max(0, (width - list.squareSize) / 2)

    visible: !isPinned
    width: ListView.view.width
    height: isPinned ? 0 : (collapsed ? list.squareSize : implicitHeight)
    leftInset: collapsed ? collapsedInset : 0
    rightInset: leftInset
    topInset: 0
    bottomInset: 0
    z: drag.active ? 10 : 0
    highlighted: isCurrent
    down: false
    focusPolicy: Qt.NoFocus
    Accessible.name: info.title
    ToolTip.visible: collapsed && hovered
    ToolTip.text: info.title
    ToolTip.delay: 600
    transform: Translate { y: drag.shift }
    onClicked: {
        tabModel.setCurrentIndex(index)
        list.focusWithPointer()
    }

    TabInfo {
        id: info
        tab: row.tab
    }

    contentItem: RowLayout {
        spacing: Kirigami.Units.smallSpacing

        TabIcon {
            tab: row.tab
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: row.collapsed
        }

        Label {
            visible: !row.collapsed
            Layout.fillWidth: true
            text: info.title
            elide: Text.ElideRight
        }

        ToolButton {
            visible: !row.collapsed
            enabled: row.isCurrent || row.hovered
            opacity: enabled ? 1 : 0
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
            flat: true
            display: AbstractButton.IconOnly
            icon.name: "window-close-symbolic"
            icon.width: 14
            icon.height: 14
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Close Tab")
            ToolTip.delay: 600
            Accessible.name: ToolTip.text
            onClicked: row.targetWindow.closeTabFor(row.tab)
        }
    }

    Rectangle {
        anchors.fill: row.background
        visible: row.hasKeyboardFocus
        color: "transparent"
        border.color: Kirigami.Theme.focusColor
        radius: Kirigami.Units.cornerRadius
    }

    TapHandler {
        acceptedButtons: Qt.MiddleButton
        onTapped: row.targetWindow.closeTabFor(row.tab)
    }

    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: eventPoint => row.targetWindow.openTabContextMenu(row.tab, eventPoint.scenePosition)
    }

    SideBarRowDrag {
        id: drag
        row: row
        tabModel: row.tabModel
    }
}
