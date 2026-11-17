import QtQuick
import Kondor

HoverHandler {
    required property AgentPointerBridge bridge

    onPointChanged: bridge.noteRealInput()
}
