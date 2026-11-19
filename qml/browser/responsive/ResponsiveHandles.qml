import QtQuick
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: root

    required property TabResponsive responsive
    required property real fitScale
    required property bool isCentered

    readonly property real thickness: 4
    readonly property real length: Kirigami.Units.gridUnit * 2

    ResponsiveHandle {
        anchors.left: parent.right
        anchors.leftMargin: 3
        anchors.verticalCenter: parent.verticalCenter
        width: root.thickness; height: root.length
        resizesWidth: true
        cursor: Qt.SizeHorCursor
        responsive: root.responsive; fitScale: root.fitScale; isCentered: root.isCentered
    }
    ResponsiveHandle {
        anchors.top: parent.bottom
        anchors.topMargin: 3
        anchors.horizontalCenter: parent.horizontalCenter
        width: root.length; height: root.thickness
        resizesHeight: true
        cursor: Qt.SizeVerCursor
        responsive: root.responsive; fitScale: root.fitScale; isCentered: root.isCentered
    }
    ResponsiveHandle {
        anchors.left: parent.right
        anchors.top: parent.bottom
        anchors.leftMargin: 3
        anchors.topMargin: 3
        width: root.thickness * 2; height: root.thickness * 2
        resizesWidth: true; resizesHeight: true
        responsive: root.responsive; fitScale: root.fitScale; isCentered: root.isCentered
    }
}
