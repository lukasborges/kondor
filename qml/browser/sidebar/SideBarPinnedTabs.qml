import QtQuick
import Kondor

Flow {
    id: root

    required property TabModel tabModel
    required property var targetWindow

    visible: tabModel.pinnedCount > 0
    spacing: 2

    Repeater {
        model: root.tabModel

        delegate: SideBarTabButton {
            visible: tab.pinned
            tabModel: root.tabModel
            targetWindow: root.targetWindow
        }
    }
}
