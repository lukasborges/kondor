// The tab bar: fixed-width tabs that shrink together down to a minimum, scroll
// arrows when they still do not fit, the New Tab button and the drop indicator.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Rectangle {
    id: strip

    required property TabModel tabModel
    // The BrowserWindow: closeTabFor() and openTabContextMenu().
    property var targetWindow: null
    property bool privateWindow: false

    signal newTabRequested()

    // Tab widths, in one place (#83). 240 is Chrome's standard tab width.
    readonly property int standardTabWidth: 240
    readonly property int minimumTabWidth: 120
    readonly property int pinnedTabWidth: 36

    readonly property alias tabBar: tabBar
    readonly property alias newTabButton: newTabButton
    readonly property alias scrollLeftButton: scrollLeftButton
    readonly property alias scrollRightButton: scrollRightButton
    property alias dropTargetIndex: tabBar.dropTargetIndex

    readonly property int pinnedCount: tabModel.pinnedCount
    readonly property int unpinnedCount: Math.max(0, tabModel.count - pinnedCount)

    // Room for the tabs before the scroll buttons are considered.
    readonly property real baseAreaWidth: Math.max(0, strip.width
        - (privateIcon.visible ? privateIcon.Layout.leftMargin + privateIcon.Layout.preferredWidth
                                 + privateIcon.Layout.rightMargin : 0)
        - newTabButton.implicitWidth - newTabButton.Layout.leftMargin)
    // The tabs overflow when they do not fit even at the minimum width.
    readonly property bool overflowing:
        pinnedCount * pinnedTabWidth + unpinnedCount * minimumTabWidth > baseAreaWidth
    readonly property real tabsAreaWidth: Math.max(0, overflowing
        ? baseAreaWidth - scrollLeftButton.implicitWidth - scrollRightButton.implicitWidth
        : baseAreaWidth)

    // Width of every unpinned tab: min(240, max(120, available / unpinned)).
    function computeTabWidth(available, unpinned, pinned) {
        const share = (available - pinned * pinnedTabWidth) / Math.max(1, unpinned)
        return Math.min(standardTabWidth, Math.max(minimumTabWidth, Math.floor(share)))
    }

    // Closing with the mouse keeps the widths until the pointer leaves (like
    // Chrome), so the next close button stays under the pointer. 0 = not frozen.
    property real frozenTabWidth: 0
    readonly property real tabWidth: {
        const computed = computeTabWidth(tabsAreaWidth, unpinnedCount, pinnedCount)
        return frozenTabWidth > 0 ? frozenTabWidth : computed
    }
    property bool closingWithMouse: false

    // Close a tab from its close button or a middle click.
    function closeWithMouse(tab) {
        if (tabWidth < standardTabWidth && tabModel.count > 1) {
            frozenTabWidth = tabWidth
            closingWithMouse = true
            unfreezeTimer.restart()
        }
        targetWindow.closeTabFor(tab)
        closingWithMouse = false
    }

    function unfreeze() {
        frozenTabWidth = 0
        unfreezeTimer.stop()
    }

    Connections {
        target: strip.tabModel
        function onCountChanged() {
            // Any other change (Ctrl+W, a new tab) recomputes the widths now.
            if (!strip.closingWithMouse)
                strip.unfreeze()
            strip.scheduleEnsureVisible()
        }
        function onCurrentIndexChanged() {
            if (tabBar.currentIndex !== strip.tabModel.currentIndex)
                tabBar.currentIndex = strip.tabModel.currentIndex
            strip.scheduleEnsureVisible()
        }
    }

    Timer {
        id: unfreezeTimer
        interval: 1000
        onTriggered: if (!barHover.hovered) strip.unfreeze()
    }

    HoverHandler {
        id: barHover
        onHoveredChanged: if (!hovered) strip.unfreeze()
    }

    // ── Scrolling ────────────────────────────────────────────────────────
    readonly property Item view: tabBar.contentItem
    // Computed from the model, not read from the ListView: the ListView
    // lays its items out a little after the widths change.
    function tabX(index) {
        return index < pinnedCount ? index * pinnedTabWidth
                                   : pinnedCount * pinnedTabWidth + (index - pinnedCount) * tabWidth
    }
    readonly property real stripWidth: tabX(tabModel.count)
    readonly property real viewWidth: Math.min(stripWidth, tabsAreaWidth)
    readonly property real maxScroll: Math.max(0, stripWidth - viewWidth)
    // The ListView may start its content at a non-zero originX; scroll
    // positions here are relative to it.
    readonly property real origin: view ? view.originX : 0
    readonly property real scrolled: view ? view.contentX - view.originX : 0

    NumberAnimation {
        id: scrollAnimation
        target: strip.view
        property: "contentX"
        duration: Kirigami.Units.shortDuration
        easing.type: Easing.OutCubic
    }

    function scrollTo(x) {
        if (!view)
            return
        const clamped = view.originX + Math.max(0, Math.min(maxScroll, x))
        scrollAnimation.stop()
        if (Math.abs(clamped - view.contentX) < 0.5)
            return
        scrollAnimation.from = view.contentX
        scrollAnimation.to = clamped
        scrollAnimation.start()
    }

    // Where the strip is heading: the end of a running animation, else its position.
    function scrollTarget() {
        return view ? (scrollAnimation.running ? scrollAnimation.to : view.contentX) - view.originX : 0
    }

    function scrollBy(delta) {
        scrollTo(scrollTarget() + delta)
    }

    // Scroll just enough to show the whole current tab.
    function ensureCurrentVisible() {
        const index = tabModel.currentIndex
        if (!view || index < 0)
            return
        view.forceLayout()
        const left = tabX(index)
        const right = tabX(index + 1)
        const current = scrollTarget()
        if (left < current)
            scrollTo(left)
        else if (right > current + viewWidth)
            scrollTo(right - viewWidth)
        else
            scrollTo(current)   // also pulls the strip back after it got shorter
    }

    // The ListView lays out after the model changes: look again once it has.
    Connections {
        target: strip.view
        function onContentWidthChanged() { strip.scheduleEnsureVisible() }
    }

    function scheduleEnsureVisible() {
        Qt.callLater(ensureCurrentVisible)
    }

    onTabsAreaWidthChanged: {
        unfreeze()
        scheduleEnsureVisible()
    }
    onTabWidthChanged: scheduleEnsureVisible()

    // True when the scene point is on the empty part of the strip, not on a
    // tab, a scroll button or the new-tab button.
    function emptyAt(sceneX, sceneY) {
        const buttons = [newTabButton, scrollLeftButton, scrollRightButton]
        for (const button of buttons) {
            if (!button.visible)
                continue
            const p = button.mapFromItem(null, sceneX, sceneY)
            if (p.x >= 0 && p.x <= button.width && p.y >= 0 && p.y <= button.height)
                return false
        }
        if (view) {
            const point = view.mapFromItem(null, sceneX, sceneY)
            if (point.x >= 0 && point.x <= view.width && point.x + view.contentX <= view.originX + view.contentWidth)
                return false
        }
        return true
    }

    implicitHeight: tabBar.implicitHeight
    Kirigami.Theme.colorSet: Kirigami.Theme.Header
    Kirigami.Theme.inherit: false
    color: Kirigami.Theme.backgroundColor

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // A private window shows the mode here, next to its tabs.
        Kirigami.Icon {
            id: privateIcon
            visible: strip.privateWindow
            source: "view-private"
            Layout.preferredWidth: 22
            Layout.preferredHeight: 22
            Layout.leftMargin: 8
            Layout.rightMargin: 4
        }

        TabBar {
            id: tabBar
            // Let the bar shrink when the tabs no longer fit; the internal
            // ListView scrolls then.
            Layout.minimumWidth: 0
            Layout.maximumWidth: strip.tabsAreaWidth
            // Index a dragged tab would land on; drives the drop indicator.
            property int dropTargetIndex: -1

            currentIndex: strip.tabModel.currentIndex
            background: null

            onCurrentIndexChanged: {
                if (strip.tabModel.currentIndex !== currentIndex)
                    strip.tabModel.setCurrentIndex(currentIndex)
            }

            Component.onCompleted: {
                if (contentItem) {
                    // Let the internal ListView flick when the tabs overflow.
                    contentItem.interactive = true
                    // The strip scrolls itself (ensureCurrentVisible): the
                    // style's highlight range would fight it.
                    contentItem.highlightRangeMode = ListView.NoHighlightRange
                }
            }

            Repeater {
                model: strip.tabModel

                delegate: TabButtonDelegate {
                    tabModel: strip.tabModel
                    tabBarItem: tabBar
                    tabStrip: strip
                    targetWindow: strip.targetWindow
                    pinnedCount: strip.pinnedCount
                }
            }

            // A mouse wheel over the tab bar scrolls it horizontally.
            WheelHandler {
                acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
                onWheel: function(event) {
                    const view = tabBar.contentItem
                    if (!view || strip.maxScroll <= 0)
                        return
                    const delta = event.pixelDelta.x !== 0 ? event.pixelDelta.x
                        : event.pixelDelta.y !== 0 ? -event.pixelDelta.y
                        : event.angleDelta.x !== 0 ? event.angleDelta.x
                        : -event.angleDelta.y
                    scrollAnimation.stop()
                    view.contentX = view.originX
                        + Math.max(0, Math.min(strip.maxScroll, strip.scrolled + delta))
                }
            }
        }

        // Scroll arrows, only while the tabs overflow.
        ToolButton {
            id: scrollLeftButton
            visible: strip.overflowing
            Layout.preferredWidth: visible ? implicitWidth : 0
            Layout.alignment: Qt.AlignVCenter
            enabled: strip.view ? strip.scrolled > 0.5 : false
            autoRepeat: true
            display: AbstractButton.IconOnly
            icon.name: "go-previous-symbolic"
            icon.width: 16
            icon.height: 16
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Scroll Tabs Left")
            ToolTip.delay: 600
            onClicked: strip.scrollBy(-strip.minimumTabWidth)
        }

        ToolButton {
            id: scrollRightButton
            visible: strip.overflowing
            Layout.preferredWidth: visible ? implicitWidth : 0
            Layout.alignment: Qt.AlignVCenter
            enabled: strip.view ? strip.scrolled < strip.maxScroll - 0.5 : false
            autoRepeat: true
            display: AbstractButton.IconOnly
            icon.name: "go-next-symbolic"
            icon.width: 16
            icon.height: 16
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Scroll Tabs Right")
            ToolTip.delay: 600
            onClicked: strip.scrollBy(strip.minimumTabWidth)
        }

        // New-tab button, right after the last tab.
        ToolButton {
            id: newTabButton
            Layout.alignment: Qt.AlignVCenter
            Layout.leftMargin: 2
            Layout.minimumWidth: implicitWidth
            display: AbstractButton.IconOnly
            icon.name: "tab-new"
            icon.width: 16
            icon.height: 16
            ToolTip.visible: hovered
            ToolTip.text: qsTr("New Tab")
            ToolTip.delay: 600
            onClicked: strip.newTabRequested()
        }

        Item { Layout.fillWidth: true }
    }

    // Where a dragged tab will land.
    Rectangle {
        readonly property Item targetItem: tabBar.dropTargetIndex >= 0 && tabBar.contentItem
            ? tabBar.itemAt(tabBar.dropTargetIndex) : null
        visible: targetItem !== null
        x: tabBar.x + (targetItem ? targetItem.x - tabBar.contentItem.contentX : 0)
        y: tabBar.y
        width: 2
        height: tabBar.height
        color: Kirigami.Theme.highlightColor
    }

    // Double-click (or middle click) on the empty part opens a new tab.
    TapHandler {
        acceptedButtons: Qt.LeftButton
        onDoubleTapped: function(eventPoint) {
            if (strip.emptyAt(eventPoint.scenePosition.x, eventPoint.scenePosition.y))
                strip.newTabRequested()
        }
    }

    TapHandler {
        acceptedButtons: Qt.MiddleButton
        onTapped: function(eventPoint) {
            if (strip.emptyAt(eventPoint.scenePosition.x, eventPoint.scenePosition.y))
                strip.newTabRequested()
        }
    }
}
