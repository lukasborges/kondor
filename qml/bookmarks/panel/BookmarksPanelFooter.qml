import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

RowLayout {
    id: root

    property bool isFolder: false
    property bool canOpenAll: false

    signal openAllRequested()
    signal manageRequested()

    Layout.margins: Kirigami.Units.smallSpacing

    Button {
        visible: root.isFolder
        enabled: root.canOpenAll
        text: qsTr("Open All in Tabs")
        icon.name: "tab-new"
        flat: true
        onClicked: root.openAllRequested()
    }

    Switch {
        visible: !root.isFolder
        text: qsTr("Show Bookmarks Bar")
        checked: Settings.showBookmarksBar
        onToggled: Settings.showBookmarksBar = checked
    }

    Item { Layout.fillWidth: true }

    ToolButton {
        display: AbstractButton.IconOnly
        icon.name: "configure"
        ToolTip.visible: hovered
        ToolTip.text: qsTr("Manage Bookmarks")
        ToolTip.delay: 600
        Accessible.name: ToolTip.text
        onClicked: root.manageRequested()
    }
}
