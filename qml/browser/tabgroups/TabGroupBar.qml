import QtQuick
import org.kde.kirigami as Kirigami
import "groupcolors.js" as GroupColors

Rectangle {
    id: bar

    property QtObject group: null
    property bool isVertical: false

    visible: group !== null
    anchors.left: parent.left
    anchors.bottom: parent.bottom
    anchors.top: isVertical ? parent.top : undefined
    anchors.right: isVertical ? undefined : parent.right
    anchors.margins: Kirigami.Units.smallSpacing
    anchors.bottomMargin: isVertical ? Kirigami.Units.smallSpacing : 0
    width: isVertical ? 3 : undefined
    height: isVertical ? undefined : 3
    radius: 1.5
    color: GroupColors.of((bar.group ? bar.group.color : "blue"), Kirigami.Theme)

}
