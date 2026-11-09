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

    // Browser window and tab bar helpers, passed in from Main.qml.
    property var tabBarItem: null
    property var targetWindow: null
    property int tabCount: 1
    property int pinnedCount: 0
    property real tabsAreaWidth: 0

    readonly property int pinnedTabWidth: 36
    readonly property int minimumTabWidth: 90
    readonly property int maximumTabWidth: 220
    readonly property string fullTitle: tab.newTabPage
        ? (tab.isPrivate ? qsTr("New Private Tab") : qsTr("New Tab"))
        : (tab.title.length ? tab.title : qsTr("New Tab"))

    // Unpinned tabs share the room left by the pinned ones. They shrink down
    // to the minimum and the tab bar starts scrolling after that.
    readonly property real sharedWidth: {
        const unpinned = Math.max(1, tabCount - pinnedCount)
        return Math.max(minimumTabWidth, (tabsAreaWidth - pinnedCount * pinnedTabWidth) / unpinned)
    }
    readonly property real naturalWidth: Math.min(maximumTabWidth, Math.max(130, Math.ceil(titleMetrics.advanceWidth) + 62))

    width: tab.pinned ? pinnedTabWidth : Math.max(minimumTabWidth, Math.min(naturalWidth, sharedWidth))
    text: ""
    Accessible.name: fullTitle

    TextMetrics {
        id: titleMetrics
        font: Kirigami.Theme.defaultFont
        text: control.fullTitle
    }

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
                visible: !control.tab.loading
                source: control.tab.isPrivate
                    ? "view-private"
                    : control.tab.newTabPage
                        ? "tab-new"
                        : (control.tab.iconUrl.toString().length ? control.tab.iconUrl.toString() : "text-html")
            }

            BusyIndicator {
                anchors.centerIn: parent
                width: 16
                height: 16
                visible: control.tab.loading
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
            onClicked: control.targetWindow.closeTabFor(control.tab)
        }
    }

    TapHandler {
        acceptedButtons: Qt.MiddleButton
        onTapped: control.targetWindow.closeTabFor(control.tab)
    }

    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: function(eventPoint) {
            control.targetWindow.openTabContextMenu(control.tab, eventPoint.scenePosition)
        }
    }

    DragHandler {
        id: dragHandler
        target: null
        xAxis.enabled: true
        yAxis.enabled: false

        property int targetIndex: -1

        function tabIndexAt(sceneX, sceneY) {
            if (!control.tabBarItem)
                return -1
            const content = control.tabBarItem.contentItem
            if (!content)
                return -1

            const point = content.mapFromItem(null, sceneX, sceneY)
            let best = -1
            let bestDistance = Number.MAX_VALUE
            for (let i = 0; i < control.tabBarItem.count; ++i) {
                const item = control.tabBarItem.itemAt(i)
                if (!item)
                    continue
                const distance = Math.abs(point.x - (item.x + item.width / 2))
                if (distance < bestDistance) {
                    bestDistance = distance
                    best = i
                }
            }
            return best
        }

        onCentroidChanged: {
            if (!active)
                return

            let target = tabIndexAt(centroid.scenePosition.x, centroid.scenePosition.y)
            if (target < 0)
                return

            // Pinned and unpinned tabs cannot be mixed by dragging.
            if (control.tab.pinned)
                target = Math.min(target, control.pinnedCount - 1)
            else
                target = Math.max(target, control.pinnedCount)

            targetIndex = target === control.tabModel.indexOfTab(control.tab) ? -1 : target
            if (control.tabBarItem)
                control.tabBarItem.dropTargetIndex = targetIndex
        }

        onActiveChanged: {
            if (active) {
                control.opacity = 0.6
                return
            }

            control.opacity = 1.0
            if (control.tabBarItem)
                control.tabBarItem.dropTargetIndex = -1

            const ownIndex = control.tabModel.indexOfTab(control.tab)
            if (targetIndex >= 0 && targetIndex !== ownIndex)
                control.tabModel.moveTab(ownIndex, targetIndex)
            targetIndex = -1
        }
    }
}
