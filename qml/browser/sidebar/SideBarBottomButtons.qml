import QtQuick
import QtQuick.Layouts
import Kondor

GridLayout {
    id: root

    property bool collapsed: false

    readonly property alias searchButton: searchButton

    signal tabSearchRequested

    columns: collapsed ? 1 : 2
    rowSpacing: 0
    columnSpacing: 0

    SideBarToggleButton {}

    TabSearchButton {
        id: searchButton
        onClicked: root.tabSearchRequested()
    }
}
