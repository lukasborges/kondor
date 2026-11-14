// Browser frame for the tab styles of #211 (floating, below) and #212 (vertical).
// The classic style is BrowserFrame.qml. Static: no logic, theme colors and Breeze icons only.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    id: frame

    // "floating" | "below" | "vertical"
    property string tabStyle: "floating"
    // Tabs: [{title, icon, pinned, loading}]
    property var tabs: []
    property int currentTab: 0
    property int hoveredTab: -1
    property bool privateWindow: false
    property int tabWidth: 240
    property bool tabScrollButtons: false
    property real tabScrollX: 0
    property string address: "https://kde.org/"

    readonly property bool vertical: tabStyle === "vertical"
    readonly property var pinnedTabs: tabs.filter(t => t.pinned)
    readonly property var unpinnedTabs: tabs.filter(t => !t.pinned)

    width: 1100
    height: 560
    color: Kirigami.Theme.backgroundColor

    component TabContent: RowLayout {
        property var tab
        property bool showClose: false
        spacing: Kirigami.Units.smallSpacing

        Item {
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
            Layout.fillWidth: tab.pinned
            Kirigami.Icon {
                anchors.centerIn: parent
                width: 16; height: 16
                visible: !tab.loading
                source: frame.privateWindow ? "view-private" : (tab.icon || "text-html")
            }
            BusyIndicator {
                anchors.centerIn: parent
                width: 18; height: 18
                visible: !!tab.loading
                running: visible
            }
        }
        Label {
            visible: !tab.pinned
            Layout.fillWidth: true
            text: tab.title
            elide: Text.ElideRight
        }
        ToolButton {
            visible: !tab.pinned
            opacity: showClose ? 1 : 0
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
            flat: true
            display: AbstractButton.IconOnly
            icon.name: "window-close-symbolic"
            icon.width: 14
            icon.height: 14
        }
    }

    // A horizontal tab: a rounded card when active, flat otherwise.
    component HorizontalTab: Rectangle {
        id: htab
        required property var modelData
        required property int index
        readonly property bool active: index === frame.currentTab
        readonly property bool hovered: index === frame.hoveredTab
        readonly property bool below: frame.tabStyle === "below"

        width: modelData.pinned ? 36 : frame.tabWidth
        height: Kirigami.Units.gridUnit * 2
        radius: Kirigami.Units.cornerRadius
        color: active ? Qt.alpha(Kirigami.Theme.highlightColor, 0.2)
             : hovered ? Qt.alpha(Kirigami.Theme.textColor, 0.05) : "transparent"
        border.color: active ? Kirigami.Theme.highlightColor
                    : "transparent"

        Kirigami.Theme.inherit: false
        Kirigami.Theme.colorSet: below ? Kirigami.Theme.Window : Kirigami.Theme.Header

        TabContent {
            anchors.fill: parent
            anchors.leftMargin: htab.modelData.pinned ? 0 : Kirigami.Units.smallSpacing * 2
            anchors.rightMargin: htab.modelData.pinned ? 0 : Kirigami.Units.smallSpacing
            tab: htab.modelData
            showClose: htab.active || htab.hovered
        }
    }

    component TabRow: RowLayout {
        spacing: 2

        Kirigami.Icon {
            visible: frame.privateWindow
            source: "view-private"
            Layout.preferredWidth: 22
            Layout.preferredHeight: 22
            Layout.leftMargin: Kirigami.Units.smallSpacing
            Layout.rightMargin: Kirigami.Units.smallSpacing
        }
        ToolButton {
            visible: frame.tabScrollButtons
            display: AbstractButton.IconOnly
            icon.name: "go-previous-symbolic"
        }
        Flickable {
            Layout.fillWidth: frame.tabScrollButtons
            Layout.preferredWidth: tabRow.implicitWidth
            Layout.preferredHeight: tabRow.implicitHeight
            contentWidth: tabRow.implicitWidth
            contentX: frame.tabScrollX
            interactive: false
            clip: true
            Row {
                id: tabRow
                spacing: 2
                Repeater { model: frame.tabs; delegate: HorizontalTab {} }
            }
        }
        ToolButton {
            visible: frame.tabScrollButtons
            display: AbstractButton.IconOnly
            icon.name: "go-next-symbolic"
        }
        ToolButton {
            display: AbstractButton.IconOnly
            icon.name: "tab-new"
        }
        Item { visible: !frame.tabScrollButtons; Layout.fillWidth: true }
    }

    component NavigationRow: RowLayout {
        spacing: 2
        Kirigami.Icon {
            visible: frame.privateWindow && frame.vertical
            source: "view-private"
            Layout.preferredWidth: 22
            Layout.preferredHeight: 22
            Layout.rightMargin: Kirigami.Units.smallSpacing
        }
        ToolButton { focusPolicy: Qt.NoFocus; display: AbstractButton.IconOnly; icon.name: "go-previous" }
        ToolButton { focusPolicy: Qt.NoFocus; display: AbstractButton.IconOnly; icon.name: "go-next"; enabled: false }
        ToolButton { focusPolicy: Qt.NoFocus; display: AbstractButton.IconOnly; icon.name: "view-refresh" }
        ToolButton { focusPolicy: Qt.NoFocus; display: AbstractButton.IconOnly; icon.name: "go-home" }
        TextField {
            Layout.fillWidth: true
            Layout.leftMargin: Kirigami.Units.smallSpacing
            Layout.rightMargin: Kirigami.Units.smallSpacing
            text: frame.address
        }
        ToolButton { focusPolicy: Qt.NoFocus; display: AbstractButton.IconOnly; icon.name: "application-menu" }
    }

    component VerticalTab: ItemDelegate {
        required property var modelData
        required property int index
        width: ListView.view ? ListView.view.width : implicitWidth
        readonly property int tabIndex: index + frame.pinnedTabs.length
        highlighted: tabIndex === frame.currentTab
        contentItem: TabContent {
            tab: modelData
            showClose: parent.highlighted || parent.tabIndex === frame.hoveredTab
        }
    }

    component SideBar: ColumnLayout {
        spacing: 0

        Flow {
            visible: frame.pinnedTabs.length > 0
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            spacing: 2
            Repeater {
                model: frame.pinnedTabs
                delegate: ToolButton {
                    required property var modelData
                    required property int index
                    checked: index === frame.currentTab
                    display: AbstractButton.IconOnly
                    icon.name: frame.privateWindow ? "view-private" : modelData.icon
                }
            }
        }
        Kirigami.Separator { visible: frame.pinnedTabs.length > 0; Layout.fillWidth: true }
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: Kirigami.Units.smallSpacing
            clip: true
            spacing: 2
            model: frame.unpinnedTabs
            delegate: VerticalTab {}
            footer: ItemDelegate {
                width: ListView.view.width
                icon.name: "tab-new"
                text: "New Tab"
            }
            ScrollBar.vertical: ScrollBar {}
        }
    }

    Item { focus: true }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            visible: frame.tabStyle === "floating"
            Layout.fillWidth: true
            implicitHeight: floatingTabs.implicitHeight + Kirigami.Units.smallSpacing * 2
            Kirigami.Theme.colorSet: Kirigami.Theme.Header
            Kirigami.Theme.inherit: false
            color: Kirigami.Theme.backgroundColor
            TabRow {
                id: floatingTabs
                anchors.fill: parent
                anchors.margins: Kirigami.Units.smallSpacing
            }
        }

        ToolBar {
            Layout.fillWidth: true
            NavigationRow {
                anchors.fill: parent
                anchors.leftMargin: Kirigami.Units.smallSpacing
                anchors.rightMargin: Kirigami.Units.smallSpacing
            }
        }

        ToolBar {
            visible: frame.tabStyle === "below"
            Layout.fillWidth: true
            position: ToolBar.Footer
            TabRow {
                anchors.fill: parent
                anchors.leftMargin: Kirigami.Units.smallSpacing
                anchors.rightMargin: Kirigami.Units.smallSpacing
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            SideBar {
                visible: frame.vertical
                Layout.preferredWidth: Kirigami.Units.gridUnit * 14
                Layout.maximumWidth: Kirigami.Units.gridUnit * 14
                Layout.fillHeight: true
            }
            Kirigami.Separator { visible: frame.vertical; Layout.fillHeight: true }
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                FakePage {}
            }
        }
    }
}
