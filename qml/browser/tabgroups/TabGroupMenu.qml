import QtQuick
import QtQuick.Controls
import Kondor

Menu {
    id: menu

    property Tab tab: null
    property int tabIndex: -1
    property TabModel tabModel: null

    readonly property bool isGrouped: tab !== null && tab.group !== null
    readonly property var otherGroups: tabModel
        ? tabModel.groups.filter(group => !tab || group !== tab.group) : []

    signal newGroupRequested(QtObject group)

    title: isGrouped ? qsTr("Move Tab to Group") : qsTr("Add Tab to Group")
    icon.name: "object-group"
    enabled: tab !== null && !tab.pinned

    MenuItem {
        text: qsTr("New Group")
        icon.name: "group-new"
        onTriggered: menu.newGroupRequested(menu.tabModel.newGroupForTab(menu.tabIndex))
    }
    MenuSeparator { visible: menu.otherGroups.length > 0 }

    Repeater {
        model: menu.otherGroups

        delegate: MenuItem {
            id: item

            required property var modelData

            text: modelData.name.length > 0 ? modelData.name : qsTr("Unnamed group")
            icon.name: "color-fill"
            icon.color: tint.value
            onTriggered: menu.tabModel.addTabToGroup(menu.tabIndex, modelData)

            GroupColor {
                id: tint
                name: item.modelData.color
            }
        }
    }
}
