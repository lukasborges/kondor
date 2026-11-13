import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Rectangle {
    id: strip

    required property TabModel tabModel
    property var targetWindow: null
    property bool privateWindow: false
    property bool tabDragActive: false

    signal newTabRequested()

    readonly property int standardTabWidth: 240
    readonly property int minimumTabWidth: 120
    readonly property int pinnedTabWidth: 36

    readonly property alias tabBar: tabBar
    readonly property alias newTabButton: newTabButton
    readonly property alias scrollLeftButton: scrollLeftButton
    readonly property alias scrollRightButton: scrollRightButton
    readonly property alias scroller: scroller
    readonly property alias maxScroll: scroller.maxScroll
    readonly property alias scrolled: scroller.scrolled

    readonly property int pinnedCount: tabModel.pinnedCount
    readonly property int unpinnedCount: Math.max(0, tabModel.count - pinnedCount)

    readonly property real baseAreaWidth: Math.max(0, strip.width
        - (privateIcon.visible ? privateIcon.Layout.leftMargin + privateIcon.Layout.preferredWidth
                                 + privateIcon.Layout.rightMargin : 0)
        - newTabButton.implicitWidth - newTabButton.Layout.leftMargin)
    readonly property bool overflowing:
        pinnedCount * pinnedTabWidth + unpinnedCount * minimumTabWidth > baseAreaWidth
    readonly property real tabsAreaWidth: Math.max(0, overflowing
        ? baseAreaWidth - scrollLeftButton.implicitWidth - scrollRightButton.implicitWidth
        : baseAreaWidth)
    readonly property real tabWidth: freeze.frozenWidth > 0 ? freeze.frozenWidth
        : computeTabWidth(tabsAreaWidth, unpinnedCount, pinnedCount)

    implicitHeight: tabBar.implicitHeight
    Kirigami.Theme.colorSet: Kirigami.Theme.Header
    Kirigami.Theme.inherit: false
    color: Kirigami.Theme.backgroundColor

    function computeTabWidth(available, unpinned, pinned) {
        const share = (available - pinned * pinnedTabWidth) / Math.max(1, unpinned)
        return Math.min(standardTabWidth, Math.max(minimumTabWidth, Math.floor(share)))
    }

    function closeWithMouse(tab) { freeze.closeWithMouse(tab) }
    function scrollTo(x) { scroller.scrollTo(x) }
    function scrollBy(delta) { scroller.scrollBy(delta) }
    function emptyAt(sceneX, sceneY) { return taps.emptyAt(sceneX, sceneY) }

    function showCurrentTabInBar() {
        if (tabBar.currentIndex !== tabModel.currentIndex)
            tabBar.currentIndex = tabModel.currentIndex
    }

    onTabsAreaWidthChanged: {
        freeze.unfreeze()
        scroller.scheduleEnsureVisible()
    }
    onTabWidthChanged: scroller.scheduleEnsureVisible()

    TabWidthFreeze { id: freeze; anchors.fill: parent; tabStrip: strip }
    TabStripScroller { id: scroller; tabStrip: strip }
    TabStripTaps { id: taps; anchors.fill: parent; tabStrip: strip }

    Connections {
        target: strip.tabModel
        function onCountChanged() {
            freeze.unfreezeUnlessClosingWithMouse()
            scroller.scheduleEnsureVisible()
        }
        function onCurrentIndexChanged() {
            strip.showCurrentTabInBar()
            scroller.scheduleEnsureVisible()
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

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
            Layout.minimumWidth: 0
            Layout.maximumWidth: strip.tabsAreaWidth
            currentIndex: strip.tabModel.currentIndex
            background: null

            function configureView() {
                contentItem.interactive = true
                contentItem.highlightRangeMode = ListView.NoHighlightRange
                contentItem.clip = true
                contentItem.spacing = 0
            }

            onCurrentIndexChanged: {
                if (strip.tabModel.currentIndex !== currentIndex)
                    strip.tabModel.setCurrentIndex(currentIndex)
            }

            Component.onCompleted: if (contentItem) configureView()

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

            TabStripWheel { tabStrip: strip }
        }

        TabStripScrollButton {
            id: scrollLeftButton
            tabStrip: strip
            enabled: strip.scroller.view ? strip.scrolled > 0.5 : false
            icon.name: "go-previous-symbolic"
            ToolTip.text: qsTr("Scroll Tabs Left")
            onClicked: strip.scrollBy(-strip.minimumTabWidth)
        }

        TabStripScrollButton {
            id: scrollRightButton
            tabStrip: strip
            enabled: strip.scroller.view ? strip.scrolled < strip.maxScroll - 0.5 : false
            icon.name: "go-next-symbolic"
            ToolTip.text: qsTr("Scroll Tabs Right")
            onClicked: strip.scrollBy(strip.minimumTabWidth)
        }

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
            Accessible.name: ToolTip.text
            ToolTip.text: qsTr("New Tab")
            ToolTip.delay: 600
            onClicked: strip.newTabRequested()
        }

        Item { Layout.fillWidth: true }
    }
}
