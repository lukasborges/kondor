// Static frame that mimics Kondor's window (qml/Main.qml) for the prototypes.
// No logic: only layout, theme colors (Kirigami.Theme) and Breeze icons.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    id: frame

    // Tabs: [{title, icon, private, pinned, loading}]
    property var tabs: [
        { title: "KDE Community", icon: "kde" },
        { title: "Wikipedia, the free encyclopedia", icon: "internet-web-browser" }
    ]
    property int currentTab: 0
    property string address: "https://kde.org/"
    property bool addressFocused: false
    property bool privateWindow: false
    property bool showHeader: true

    // Extra items inside the address bar (left / right).
    property alias addressLeft: leftSlot.data
    property alias addressRight: rightSlot.data
    // Extra toolbar buttons, before the menu button.
    property alias toolbarExtras: extrasSlot.data
    // Strip right below the header (bookmarks toolbar, InlineBar…).
    property alias belowHeader: belowSlot.data
    // Page content (a fake page by default).
    default property alias page: pageSlot.data
    readonly property alias addressField: addressBar
    readonly property alias menuButton: menuButton

    width: 1100
    height: 700
    color: Kirigami.Theme.backgroundColor

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ── Tab bar ─────────────────────────────────────────────────────
        Rectangle {
            visible: frame.showHeader
            Layout.fillWidth: true
            implicitHeight: 36
            Kirigami.Theme.colorSet: Kirigami.Theme.Header
            Kirigami.Theme.inherit: false
            color: Kirigami.Theme.backgroundColor

            RowLayout {
                anchors.fill: parent
                spacing: 0

                Kirigami.Icon {
                    visible: frame.privateWindow
                    source: "view-private"
                    Layout.preferredWidth: 22
                    Layout.preferredHeight: 22
                    Layout.leftMargin: 8
                    Layout.rightMargin: 4
                }

                TabBar {
                    id: tabBar
                    currentIndex: frame.currentTab
                    background: null
                    Repeater {
                        model: frame.tabs
                        delegate: TabButton {
                            required property var modelData
                            width: modelData.pinned ? 40 : 200
                            display: modelData.pinned ? AbstractButton.IconOnly : AbstractButton.TextBesideIcon
                            icon.name: modelData.private ? "view-private" : (modelData.icon || "text-html")
                            icon.width: 16
                            icon.height: 16
                            // The Breeze style would draw the text again; the contentItem below handles it.
                            text: ""
                            contentItem: RowLayout {
                                spacing: 6
                                Item { visible: !modelData.pinned; Layout.preferredWidth: 2 }
                                Item {
                                    Layout.preferredWidth: 16
                                    Layout.preferredHeight: 16
                                    Layout.alignment: modelData.pinned ? Qt.AlignHCenter : Qt.AlignLeft
                                    Layout.fillWidth: modelData.pinned
                                    Kirigami.Icon {
                                        anchors.centerIn: parent
                                        width: 16; height: 16
                                        visible: !modelData.loading
                                        source: modelData.private ? "view-private" : (modelData.icon || "text-html")
                                    }
                                    BusyIndicator {
                                        anchors.centerIn: parent
                                        width: 18; height: 18
                                        visible: !!modelData.loading
                                        running: visible
                                    }
                                }
                                Label {
                                    visible: !modelData.pinned
                                    Layout.fillWidth: true
                                    text: modelData.title
                                    elide: Text.ElideRight
                                }
                                ToolButton {
                                    visible: !modelData.pinned
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 20
                                    flat: true
                                    display: AbstractButton.IconOnly
                                    icon.name: "window-close-symbolic"
                                    icon.width: 14
                                    icon.height: 14
                                }
                            }
                        }
                    }
                }

                ToolButton {
                    display: AbstractButton.IconOnly
                    icon.name: "tab-new"
                    icon.width: 16
                    icon.height: 16
                }
                Item { Layout.fillWidth: true }
            }
        }

        // ── Navigation toolbar ──────────────────────────────────────────
        ToolBar {
            visible: frame.showHeader
            Layout.fillWidth: true
            Kirigami.Theme.colorSet: Kirigami.Theme.Window
            Kirigami.Theme.inherit: false

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 5
                anchors.rightMargin: 5
                spacing: 2

                ToolButton { display: AbstractButton.IconOnly; icon.name: "go-previous" }
                ToolButton { display: AbstractButton.IconOnly; icon.name: "go-next"; enabled: false }
                ToolButton { display: AbstractButton.IconOnly; icon.name: "view-refresh" }
                ToolButton { display: AbstractButton.IconOnly; icon.name: "go-home" }

                TextField {
                    id: addressBar
                    Layout.fillWidth: true
                    Layout.leftMargin: 8
                    Layout.rightMargin: 8
                    text: frame.address
                    focus: frame.addressFocused
                    leftPadding: leftSlot.children.length ? leftSlot.width + 10 : 8
                    rightPadding: rightSlot.children.length ? rightSlot.width + 10 : 8

                    Row {
                        id: leftSlot
                        anchors.left: parent.left
                        anchors.leftMargin: 3
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 0
                    }
                    Row {
                        id: rightSlot
                        anchors.right: parent.right
                        anchors.rightMargin: 3
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 0
                    }
                }

                Row { id: extrasSlot; spacing: 2 }

                ToolButton {
                    id: menuButton
                    display: AbstractButton.IconOnly
                    icon.name: "application-menu"
                }
            }
        }

        ColumnLayout {
            id: belowSlot
            Layout.fillWidth: true
            Layout.fillHeight: false
            spacing: 0
        }

        // ── Page ─────────────────────────────────────────────────────────
        Item {
            id: pageSlot
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
        }
    }
}
