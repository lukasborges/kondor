import QtQuick
import org.kde.kirigami as Kirigami

Rectangle {
    id: root

    required property color pointerColor
    property point center: Qt.point(0, 0)

    function play(point) {
        center = point
        animation.restart()
    }

    x: center.x - width / 2
    y: center.y - height / 2
    width: 40
    height: width
    radius: width / 2
    color: "transparent"
    border.width: 3
    border.color: root.pointerColor
    opacity: 0

    ParallelAnimation {
        id: animation

        NumberAnimation {
            target: root
            property: "width"
            from: 40
            to: 64
            duration: Kirigami.Units.longDuration
        }

        NumberAnimation {
            target: root
            property: "opacity"
            from: 0.7
            to: 0
            duration: Kirigami.Units.longDuration
        }
    }
}
