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

    readonly property string fullTitle: tab.newTabPage
        ? (tab.isPrivate ? qsTr("New Private Tab") : qsTr("New Tab"))
        : (tab.title.length ? tab.title : qsTr("New Tab"))
    readonly property string iconSource: {
        if (tab.crashed)
            return "dialog-error"
        if (tab.isPrivate)
            return "view-private"
        if (tab.newTabPage)
            return "tab-new"
        return tab.iconUrl.toString().length ? tab.iconUrl.toString() : "text-html"
    }

    width: tab.pinned ? tabStrip.pinnedTabWidth : tabStrip.tabWidth
    text: ""
    Accessible.name: fullTitle
    z: tabDrag.active || tabSlide.isSettling ? 10 : 0
    transform: [
        Translate { x: control.dragShift },
        Translate { x: control.slideShift }
    ]

    onXChanged: tabSlide.followPosition()
    Component.onDestruction: tabDrag.abortOnDestruction()

    contentItem: RowLayout {
        spacing: 6

        Item {
            visible: !control.tab.pinned
            Layout.preferredWidth: 2
        }

        Item {
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
            Layout.alignment: control.tab.pinned ? Qt.AlignHCenter : Qt.AlignLeft
            Layout.fillWidth: control.tab.pinned

            Kirigami.Icon {
                anchors.centerIn: parent
                width: 16
                height: 16
                visible: !control.tab.loading || control.tab.crashed
                source: control.iconSource
            }

            BusyIndicator {
                anchors.centerIn: parent
                width: 16
                height: 16
                visible: control.tab.loading && !control.tab.crashed
                running: visible
            }
        }

        Label {
            visible: !control.tab.pinned
            Layout.fillWidth: true
            text: control.fullTitle
            elide: Text.ElideRight
        }

        ToolButton {
            visible: !control.tab.pinned
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
