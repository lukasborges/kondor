import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ItemDelegate {
    id: row

    required property Tab tab
    required property int index
    required property int tabIndex
    required property TabModel tabModel
    required property var targetWindow
    required property ListView list

    readonly property bool isPinned: tab?.pinned ?? false
    readonly property bool isCurrent: tabIndex === tabModel.currentIndex
    readonly property color textColor: isCurrent ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
    readonly property bool hasKeyboardFocus: list.isFocusRingVisible && index === list.currentIndex

    required property bool isHidden
    readonly property real groupShift: list.groupDrag.shiftOf(tab.group)

    visible: height > 0
    width: ListView.view.width
    height: isPinned || isHidden ? 0 : implicitHeight
    z: drag.active ? 10 : 0
    highlighted: isCurrent
    down: false
    focusPolicy: Qt.NoFocus
    Accessible.name: info.title
    Accessible.description: info.stateDescription
    transform: Translate { y: drag.shift + row.groupShift }
    onClicked: {
        tabModel.setCurrentIndex(tabIndex)
        list.focusWithPointer()
    }

    Binding {
        when: row.tab.group !== null
        target: row
        property: "leftPadding"
        value: row.horizontalPadding + Kirigami.Units.largeSpacing
    }

    TabGroupBar {
        isVertical: true
        group: row.tab.group
        anchors.topMargin: Kirigami.Units.smallSpacing
    }

    TabInfo {
        id: info
        tab: row.tab
    }

    ToolTip.visible: hovered && info.isAgentTab
    ToolTip.text: info.agentDescription
    ToolTip.delay: 600

    contentItem: RowLayout {
        spacing: Kirigami.Units.smallSpacing

        TabIcon {
            tab: row.tab
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
            Layout.alignment: Qt.AlignHCenter
        }

        AgentTabIcon {
            visible: info.isAgentTab
        }

        TabSoundButton {
            visible: info.hasSoundState
            tab: row.tab
            iconColor: row.textColor
        }

        Label {
            Layout.fillWidth: true
            text: info.title
            enabled: !info.isSleeping
            color: enabled ? row.textColor : Kirigami.Theme.disabledTextColor
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
            icon.color: row.textColor
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
