import QtQuick

QtObject {
    property var group: null
    property real shift: 0

    function shiftOf(candidate) {
        return candidate !== null && candidate === group ? shift : 0
    }

    function begin(dragged) {
        group = dragged
    }

    function end() {
        group = null
        shift = 0
    }
}
