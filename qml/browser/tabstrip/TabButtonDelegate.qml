import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

TabButton {
    id: control

    required property Tab tab
    required property TabModel tabModel

    property var tabBarItem: null
    property var targetWindow: null
    property var tabStrip: null
    property int pinnedCount: 0
    property real dragShift: 0
    property real slideShift: 0

    readonly property bool isStyled: tabStrip.isStyled
    readonly property bool showsCloseButton: !isStyled || checked || hovered

    width: tab.pinned ? tabStrip.pinnedTabWidth : tabStrip.tabWidth
    text: ""
    leftPadding: isStyled && !tab.pinned ? Kirigami.Units.smallSpacing * 2 : implicitLeftPadding
    rightPadding: isStyled && !tab.pinned ? Kirigami.Units.smallSpacing : implicitRightPadding
    Accessible.name: info.title
    z: tabDrag.active || tabSlide.isSettling ? 10 : 0
    transform: [
        Translate { x: control.dragShift },
        Translate { x: control.slideShift }
    ]

    Binding {
        target: control.background
        property: "visible"
        value: !control.isStyled
    }

    Binding {
        when: control.isStyled
        target: control
        property: "implicitHeight"
        value: Kirigami.Units.gridUnit * 2
    }

    TabCard {
        id: tabCard
        anchors.fill: parent
        z: -1
        visible: control.isStyled
        isActive: control.checked
        isHovered: control.hovered
        hasKeyboardFocus: control.visualFocus
    }

    TabInfo {
        id: info
        tab: control.tab
    }

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
            }
        }

        Label {
            visible: !control.tab.pinned
            Layout.fillWidth: true
            text: info.title
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

    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: function(eventPoint) {
            control.targetWindow.openTabContextMenu(control.tab, eventPoint.scenePosition)
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
