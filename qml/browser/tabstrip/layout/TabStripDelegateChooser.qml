import QtQuick
import QtQml.Models
import Kondor

DelegateChooser {
    id: chooser

    required property var tabStrip

    role: "kind"

    DelegateChoice {
        roleValue: "label"

        TabStripLabelDelegate {
            tabStrip: chooser.tabStrip
        }
    }

    DelegateChoice {
        roleValue: "tab"

        TabButtonDelegate {
            tabModel: chooser.tabStrip.tabModel
            tabBarItem: chooser.tabStrip.tabBar
            tabStrip: chooser.tabStrip
            targetWindow: chooser.tabStrip.targetWindow
            pinnedCount: chooser.tabStrip.pinnedCount
        }
    }
}
