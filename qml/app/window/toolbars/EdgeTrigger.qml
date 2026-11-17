import QtQuick

Item {
    id: root

    readonly property alias isHovered: area.containsMouse

    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
    }
}
