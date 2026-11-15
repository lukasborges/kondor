import QtQuick
import org.kde.kirigami as Kirigami

Row {
    id: tabs

    property string tabStyle: "floating"
    property color stripColor: "transparent"
    property color toolBarColor: "transparent"

    readonly property bool isClassic: tabStyle === "classic"

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
            readonly property color activeColor: tabs.isClassic
                ? tabs.toolBarColor : Qt.alpha(Kirigami.Theme.highlightColor, 0.25)
            readonly property color activeBorderColor: tabs.isClassic
                ? "transparent" : Kirigami.Theme.highlightColor

            Rectangle {
                visible: tabs.isClassic && parent.isActive
                width: parent.width
                height: 2
                color: Kirigami.Theme.highlightColor
            }
        }
    }
}
