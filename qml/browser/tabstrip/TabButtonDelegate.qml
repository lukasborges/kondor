import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

TabButton {
    id: control

    required property Tab tab
    required property int index
    required property int tabIndex
    required property TabModel tabModel

    property var tabBarItem: null
    property var targetWindow: null
    property var tabStrip: null
    property int pinnedCount: 0
    property real dragShift: 0
    property real slideShift: 0

    readonly property bool isStyled: tabStrip.isStyled
    readonly property bool isRaised: tabDrag.active || tabSlide.isSettling
    readonly property bool showsCloseButton: !isStyled || checked || hovered
    readonly property real groupShift: tabStrip.shiftOfGroup(tab.group)

    width: tabStrip.layout.rowWidth(index)
    visible: width > 0
    text: ""
    Accessible.name: tab.pinned ? info.iconOnlyName : info.title
    Accessible.description: info.stateDescription
    z: isRaised ? 10 : 0
    transform: [
        Translate { x: control.dragShift },
        Translate { x: control.slideShift },
        Translate { x: control.groupShift }
    ]

    TabStyleBindings { control: control }

    TabCard {
        id: tabCard
        anchors.fill: parent
        z: -1
        visible: control.isStyled
        isActive: control.checked
        isHovered: control.hovered
        isRaised: control.isRaised
        underlayColor: control.tabStrip.color
        hasKeyboardFocus: control.visualFocus
    }

    TabInfo {
        id: info
        tab: control.tab
    }

    AgentTabBorder {
        visible: info.isAgentTab
        anchors.leftMargin: 1
    }

    TabGroupBar {
        group: control.tab.group
    }

    ToolTip.visible: hovered && info.isAgentTab
    ToolTip.text: info.agentDescription
    ToolTip.delay: 600

    onXChanged: tabSlide.followPosition()
    Component.onDestruction: tabDrag.abortOnDestruction()

    contentItem: RowLayout {
        spacing: control.isStyled ? Kirigami.Units.smallSpacing : 6

        Item {
            visible: !control.tab.pinned && !control.isStyled
            Layout.preferredWidth: 2
        }

        Item {
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
            Layout.alignment: control.tab.pinned ? Qt.AlignHCenter : Qt.AlignLeft
            Layout.fillWidth: control.tab.pinned

            TabIcon {
                anchors.centerIn: parent
                tab: control.tab
                showsEmblem: control.tab.pinned
            }
        }

        AgentTabIcon {
            visible: !control.tab.pinned && info.isAgentTab
        }

        TabSoundButton {
            visible: !control.tab.pinned && info.hasSoundState
            tab: control.tab
        }

        Label {
            visible: !control.tab.pinned
            Layout.fillWidth: true
            text: info.title
            enabled: !info.isSleeping
            elide: Text.ElideRight
        }

        ToolButton {
            visible: !control.tab.pinned
            enabled: control.showsCloseButton
            opacity: control.showsCloseButton ? 1 : 0
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
            flat: true
            display: AbstractButton.IconOnly
            icon.name: "window-close-symbolic"
            icon.width: 14
            icon.height: 14
            ToolTip.visible: hovered
            Accessible.name: ToolTip.text
            ToolTip.text: qsTr("Close Tab")
            ToolTip.delay: 600
            onClicked: control.tabStrip.closeWithMouse(control.tab)
        }
    }

    TapHandler {
        acceptedButtons: Qt.MiddleButton
        onTapped: control.tabStrip.closeWithMouse(control.tab)
    }

    MouseArea {
        anchors.fill: parent
        z: 1
        acceptedButtons: Qt.RightButton
        onClicked: function(mouse) {
            control.targetWindow.openTabContextMenu(control.tab, mapToItem(null, mouse.x, mouse.y))
        }
    }

    Timer {
        interval: 16
        repeat: true
        running: tabDrag.isAutoScrolling
        onTriggered: tabDrag.autoScroll()
    }

    TabDragHandler {
        id: tabDrag
        tabButton: control
        slide: tabSlide
    }

    TabSlideAnimation {
        id: tabSlide
        tabButton: control
        tabStrip: control.tabStrip
        dragHandler: tabDrag
    }
}
