import QtQuick
import Kondor

PointHandler {
    required property AgentPointerBridge bridge

    acceptedButtons: Qt.AllButtons
    onPointChanged: bridge.noteRealInput()
}
