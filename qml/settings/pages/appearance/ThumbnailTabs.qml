import QtQuick
import org.kde.kirigami as Kirigami

Row {
    id: tabs

    property string tabStyle: "floating"
    property color stripColor: "transparent"
    property color toolBarColor: "transparent"

    readonly property bool isClassic: tabStyle === "classic"
    readonly property bool isBelowAddressBar: tabStyle === "below"

    spacing: 2

    Repeater {
        model: 3

        Rectangle {
            required property int index
            readonly property bool isActive: index === 1

            width: 26
            height: 9
            radius: tabs.isClassic ? 0 : 2
            color: isActive ? activeColor : restColor
            border.color: isActive ? activeBorderColor : "transparent"

            readonly property color restColor: tabs.isClassic ? Qt.darker(tabs.stripColor, 1.05) : "transparent"
            readonly property color activeColor: tabs.isBelowAddressBar
                ? Qt.alpha(Kirigami.Theme.highlightColor, 0.25) : tabs.toolBarColor
            readonly property color activeBorderColor: tabs.isBelowAddressBar
                ? Kirigami.Theme.highlightColor
                : tabs.isClassic ? "transparent" : Qt.alpha(Kirigami.Theme.textColor, 0.3)

            Rectangle {
                visible: tabs.isClassic && parent.isActive
                width: parent.width
                height: 2
                color: Kirigami.Theme.highlightColor
            }
        }
    }
}
