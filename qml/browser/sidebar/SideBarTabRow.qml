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
    readonly property color textColor: isCurrent ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
    readonly property bool hasKeyboardFocus: list.isFocusRingVisible && index === list.currentIndex

    readonly property bool isGroupStart: tabModel.groupRevision >= 0 && tabModel.isGroupStart(index)
    readonly property bool isHiddenByGroup: tabModel.groupRevision >= 0 && tabModel.isHiddenByGroup(index)
    readonly property real headerHeight: isGroupStart ? Kirigami.Units.gridUnit * 1.8 : 0

    visible: height > 0
    width: ListView.view.width
    height: isPinned ? 0 : isHiddenByGroup ? headerHeight : implicitHeight
    topInset: headerHeight
    z: drag.active ? 10 : 0
    highlighted: isCurrent
    down: false
    focusPolicy: Qt.NoFocus
    Accessible.name: info.title
    Accessible.description: info.stateDescription
    transform: Translate { y: drag.shift }
    onClicked: {
        tabModel.setCurrentIndex(index)
        list.focusWithPointer()
    }

    Binding {
        when: row.isGroupStart
        target: row
        property: "topPadding"
        value: row.headerHeight + row.verticalPadding
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
        visible: group !== null && !row.isHiddenByGroup
        anchors.topMargin: row.headerHeight + Kirigami.Units.smallSpacing
    }

    Loader {
        active: row.isGroupStart
        width: row.width
        height: row.headerHeight
        sourceComponent: SideBarGroupHeader {
            group: row.tab.group
            tabModel: row.tabModel
            targetWindow: row.targetWindow
        }
    }

    TabInfo {
        id: info
        tab: row.tab
    }

    ToolTip.visible: hovered && info.isAgentTab
    ToolTip.text: info.agentDescription
    ToolTip.delay: 600

    contentItem: RowLayout {
        visible: !row.isHiddenByGroup
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
        visible: !row.isHiddenByGroup
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
