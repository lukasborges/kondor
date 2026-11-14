import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Rectangle {
    id: sideBar

    required property TabModel tabModel
    required property var targetWindow

    signal newTabRequested()

    implicitWidth: Kirigami.Units.gridUnit * 14
    Kirigami.Theme.colorSet: Kirigami.Theme.Window
    Kirigami.Theme.inherit: false
    color: Kirigami.Theme.backgroundColor

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        SideBarPinnedTabs {
            tabModel: sideBar.tabModel
            targetWindow: sideBar.targetWindow
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
        }

        Kirigami.Separator {
            visible: sideBar.tabModel.pinnedCount > 0
            Layout.fillWidth: true
        }

        SideBarTabList {
            tabModel: sideBar.tabModel
            targetWindow: sideBar.targetWindow
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: Kirigami.Units.smallSpacing
            onNewTabRequested: sideBar.newTabRequested()
        }
    }
}
