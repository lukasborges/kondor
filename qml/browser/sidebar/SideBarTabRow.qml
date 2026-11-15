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

    readonly property bool isPinned: tab?.pinned ?? false
    readonly property bool isCurrent: index === tabModel.currentIndex
    readonly property bool hasKeyboardFocus: list.isFocusRingVisible && index === list.currentIndex

    visible: !isPinned
    width: ListView.view.width
    height: isPinned ? 0 : implicitHeight
    z: drag.active ? 10 : 0
    highlighted: isCurrent
    down: false
    focusPolicy: Qt.NoFocus
    Accessible.name: info.title
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
        }

        Label {
            Layout.fillWidth: true
            text: info.title
            elide: Text.ElideRight
        }

        ToolButton {
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

    background: Rectangle {
        radius: Kirigami.Units.cornerRadius
        color: row.isCurrent ? Kirigami.Theme.highlightColor : row.hovered ? Qt.alpha(Kirigami.Theme.highlightColor, 0.3) : "transparent"
    }

    SideBarFocusRing {
        anchors.fill: row.background
        visible: row.hasKeyboardFocus
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
