import QtQuick
import org.kde.kirigami as Kirigami

Rectangle {
    color: "transparent"
    border.color: Kirigami.Theme.focusColor
    border.width: 2

    Rectangle {
        anchors.fill: parent
        anchors.margins: parent.border.width
        color: "transparent"
        radius: Math.max(0, parent.radius - parent.border.width)
        border.color: Kirigami.Theme.backgroundColor
    }
}
