// #385 Remote control: the agent's pointer drawn over the page, so it never looks like the user's
// own cursor: an arrow in the neutral (attention) color with a white outline and the
// automated-tasks badge, the same color as the toolbar indicator. A ring marks where it clicked.
import QtQuick
import QtQuick.Controls
import QtQuick.Shapes
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    address: "https://bugs.kde.org/"
    tabs: [{ title: "KDE Bugtracking System", icon: "internet-web-browser" }]
    toolbarExtras: [
        ToolButton {
            icon.name: "automated-tasks"
            icon.color: Kirigami.Theme.neutralTextColor
            display: AbstractButton.IconOnly
        }
    ]
    FakePage { heading: "KDE Bugtracking System" }

    Item {
        id: overlay
        anchors.fill: parent

        // Click ring: grows and fades out where the agent clicked.
        Rectangle {
            x: 520 - width / 2
            y: 300 - height / 2
            width: 40
            height: 40
            radius: width / 2
            color: "transparent"
            border.width: 3
            border.color: Kirigami.Theme.neutralTextColor
            opacity: 0.7
        }

        Item {
            id: pointer
            x: 520
            y: 300
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
    }
}
