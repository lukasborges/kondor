import QtQuick
import QtQml.Models
import Kondor

DelegateChooser {
    id: chooser

    required property ListView list
    property bool isIconOnly: false

    role: "kind"

    DelegateChoice {
        roleValue: "label"

        SideBarLabelRow {
            isIconOnly: chooser.isIconOnly
            tabModel: chooser.list.tabModel
            targetWindow: chooser.list.targetWindow
            list: chooser.list
        }
    }

    DelegateChoice {
        roleValue: "tab"
        delegate: chooser.isIconOnly ? chooser.collapsedTab : chooser.expandedTab
    }

    property Component expandedTab: SideBarTabRow {
        tabModel: chooser.list.tabModel
        targetWindow: chooser.list.targetWindow
        list: chooser.list
    }

    property Component collapsedTab: SideBarCollapsedTabRow {
        tabModel: chooser.list.tabModel
        targetWindow: chooser.list.targetWindow
        list: chooser.list
    }
}
