import QtQuick
import QtQuick.Shapes
import org.kde.kirigami as Kirigami

Item {
    Shape {
        width: 22
        height: 30
        layer.enabled: true
        layer.samples: 4

        ShapePath {
            strokeColor: "white"
            strokeWidth: 2
            fillColor: Kirigami.Theme.neutralTextColor
            joinStyle: ShapePath.RoundJoin
            startX: 0; startY: 0
            PathLine { x: 0; y: 24 }
            PathLine { x: 6; y: 18 }
            PathLine { x: 11; y: 28 }
            PathLine { x: 15; y: 26 }
            PathLine { x: 10; y: 16 }
            PathLine { x: 18; y: 16 }
            PathLine { x: 0; y: 0 }
        }
    }

    Rectangle {
        x: 16
        y: 22
        width: 22
        height: 22
        radius: width / 2
        color: Kirigami.Theme.neutralTextColor
        border.color: "white"
        border.width: 2

        Kirigami.Icon {
            anchors.centerIn: parent
            width: 14
            height: 14
            source: "automated-tasks"
            color: "white"
            isMask: true
        }
    }
}
