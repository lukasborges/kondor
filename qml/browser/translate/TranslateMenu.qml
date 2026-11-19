import QtQuick
import QtQuick.Controls
import Kondor

Menu {
    id: root

    required property TabTranslation translation

    signal manageRequested()

    popupType: Popup.Item

    MenuItem {
        visible: root.translation.lists.canChange
        height: visible ? implicitHeight : 0
        text: qsTr("Always Translate %1").arg(root.translation.lists.languageName)
        checkable: true
        checked: root.translation.lists.isAlways
        onTriggered: root.translation.lists.setAlways(checked)
    }

    MenuItem {
        visible: root.translation.lists.canChange
        height: visible ? implicitHeight : 0
        text: qsTr("Never Translate %1").arg(root.translation.lists.languageName)
        checkable: true
        checked: root.translation.lists.isNever
        onTriggered: root.translation.lists.setNever(checked)
    }

    MenuItem {
        visible: root.translation.lists.canChange && root.translation.lists.host !== ""
        height: visible ? implicitHeight : 0
        text: qsTr("Never Translate %1").arg(root.translation.lists.host)
        checkable: true
        checked: root.translation.lists.isNeverHost
        onTriggered: root.translation.lists.setNeverHost(checked)
    }

    MenuSeparator { visible: root.translation.lists.canChange }

    MenuItem {
        text: qsTr("Manage Languages…")
        icon.name: "languages"
        onTriggered: root.manageRequested()
    }
}
