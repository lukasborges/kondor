// One tab button: favicon, elided title, close button, pinned layout,
// middle/right click and drag to reorder.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

TabButton {
    id: control

    required property Tab tab
    required property TabModel tabModel

    // Browser window and tab bar helpers, passed in from BrowserWindow.qml.
    property var tabBarItem: null
    property var targetWindow: null
    // The TabStrip owns the tab widths.
    property var tabStrip: null
    property int pinnedCount: 0

    readonly property string fullTitle: tab.newTabPage
        ? (tab.isPrivate ? qsTr("New Private Tab") : qsTr("New Tab"))
        : (tab.title.length ? tab.title : qsTr("New Tab"))

    // Every unpinned tab has the same width, whatever its title (#83).
    width: tab.pinned ? tabStrip.pinnedTabWidth : tabStrip.tabWidth
    text: ""
    Accessible.name: fullTitle

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
                source: control.tab.crashed
                    ? "dialog-error"
                    : control.tab.isPrivate
                        ? "view-private"
                        : control.tab.newTabPage
                            ? "tab-new"
                            : (control.tab.iconUrl.toString().length ? control.tab.iconUrl.toString() : "text-html")
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

    // The dragged tab is drawn at the pointer through this translate: the
    // ListView owns x. It settles back to 0 when the drag ends (#91).
    property real dragShift: 0
    // Neighbours of the dragged tab slide to their new slot through this
    // offset (the ListView's move/displaced transitions crash on close).
    property real slideShift: 0
    property real lastX: 0
    transform: [
        Translate { x: control.dragShift },
        Translate { x: control.slideShift }
    ]
    z: dragHandler.active || settle.running ? 10 : 0

    NumberAnimation {
        id: settle
        target: control
        property: "dragShift"
        to: 0
        duration: Kirigami.Units.shortDuration
        easing.type: Easing.OutCubic
    }

    NumberAnimation {
        id: slideAnimation
        target: control
        property: "slideShift"
        to: 0
        duration: Kirigami.Units.shortDuration
        easing.type: Easing.OutCubic
    }

    Component.onCompleted: lastX = x

    onXChanged: {
        if (dragHandler.active) {
            dragHandler.update()
        } else if (tabStrip && tabStrip.tabDragActive) {
            slideShift += lastX - x
            slideAnimation.restart()
        }
        lastX = x
    }

    // Scrolls the strip while a tab is dragged to its left or right edge.
    Timer {
        interval: 16
        repeat: true
        running: dragHandler.active && control.tabStrip && control.tabStrip.maxScroll > 0
        onTriggered: {
            const strip = control.tabStrip
            const view = strip.view
            const x = view.mapFromItem(null, dragHandler.sceneX, dragHandler.sceneY).x
            let delta = 0
            if (x < 24)
                delta = -8
            else if (x > view.width - 24)
                delta = 8
            if (delta === 0)
                return
            strip.scrollAnimationStop()
            view.contentX = view.originX + Math.max(0, Math.min(strip.maxScroll, strip.scrolled + delta))
            dragHandler.update()
        }
    }

    DragHandler {
        id: dragHandler
        target: null
        xAxis.enabled: true
        yAxis.enabled: false

        // Last pointer position (scene) and where the tab was grabbed.
        property real sceneX: 0
        property real sceneY: 0
        property real grabOffset: 0

        // Content x of a scene point, in the ListView's content coordinates.
        function contentX(sx, sy) {
            return control.parent.mapFromItem(null, sx, sy).x
        }

        // Draw the tab at the pointer, and move it in the model when its
        // center has reached another slot.
        function update() {
            const strip = control.tabStrip
            if (!strip || !control.parent)
                return
            const pinned = control.tab.pinned
            const sectionStart = pinned ? 0 : strip.tabX(control.pinnedCount)
            const sectionEnd = pinned ? strip.tabX(control.pinnedCount) : strip.stripWidth
            const width = control.width
            const origin = strip.origin
            let left = contentX(sceneX, sceneY) - origin - grabOffset
            left = Math.max(sectionStart, Math.min(sectionEnd - width, left))

            const own = control.tabModel.indexOfTab(control.tab)
            const center = left + width / 2
            let target
            if (pinned)
                target = Math.floor(center / strip.pinnedTabWidth)
            else
                target = control.pinnedCount + Math.floor((center - sectionStart) / strip.tabWidth)
            target = pinned
                ? Math.max(0, Math.min(control.pinnedCount - 1, target))
                : Math.max(control.pinnedCount, Math.min(control.tabModel.count - 1, target))
            if (target !== own) {
                control.tabModel.moveTab(own, target)
                if (control.tabBarItem && control.tabBarItem.contentItem)
                    control.tabBarItem.contentItem.forceLayout()
            }
            // A move can change the ListView's originX: read it again.
            control.dragShift = left + strip.origin - control.x
        }

        onCentroidChanged: {
            if (!active)
                return
            sceneX = centroid.scenePosition.x
            sceneY = centroid.scenePosition.y
            update()
        }

        onActiveChanged: {
            if (control.tabStrip)
                control.tabStrip.tabDragActive = active
            if (active) {
                sceneX = centroid.scenePosition.x
                sceneY = centroid.scenePosition.y
                grabOffset = contentX(centroid.scenePressPosition.x, centroid.scenePressPosition.y) - control.x
                // Starting a drag selects the dragged tab.
                control.tabModel.setCurrentIndex(control.tabModel.indexOfTab(control.tab))
                settle.stop()
                update()
            } else {
                settle.start()
                if (control.tabStrip)
                    control.tabStrip.scheduleEnsureVisible()
            }
        }
    }
}
