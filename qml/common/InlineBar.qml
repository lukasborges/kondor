import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// Shared strip between the header and the page content (find, permissions,
// crash notices). The page keeps the View color set and thin separators.
Rectangle {
    id: root

    default property alias content: layout.data
    property alias spacing: layout.spacing

    implicitHeight: layout.implicitHeight + 2 * Kirigami.Units.smallSpacing

    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    color: Kirigami.Theme.backgroundColor

    data: [
        Kirigami.Separator {
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
            }
        },
        Kirigami.Separator {
            anchors {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
        },
        RowLayout {
            id: layout
            anchors {
                fill: parent
                leftMargin: Kirigami.Units.largeSpacing
                rightMargin: Kirigami.Units.smallSpacing
                topMargin: Kirigami.Units.smallSpacing
                bottomMargin: Kirigami.Units.smallSpacing
            }
            spacing: Kirigami.Units.smallSpacing
        }
    ]
}
