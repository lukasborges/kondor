import QtQuick
import QtQuick.Controls
import QtQml
import Kondor

Menu {
    id: root

    required property var browserWindow

    title: qsTr("Profiles")
    icon.name: "im-user"

    MenuKeyNavigation { menu: root }

    Instantiator {
        model: UserProfiles.profiles
        delegate: MenuItem {
            required property var modelData
            text: modelData.name
            icon.name: modelData.iconName
            onTriggered: UserProfiles.openWindow(modelData.id)
        }
        onObjectAdded: function(index, object) { root.insertItem(index, object) }
        onObjectRemoved: function(index, object) { root.removeItem(object) }
    }

    MenuSeparator {}

    MenuItem {
        text: qsTr("New Profile…")
        icon.name: "list-add"
        onTriggered: root.browserWindow.openNewProfile()
    }

    MenuItem {
        text: qsTr("Manage Profiles…")
        icon.name: "configure"
        onTriggered: root.browserWindow.openManageProfiles()
    }
}
