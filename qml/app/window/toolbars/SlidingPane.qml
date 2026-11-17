import QtQuick
import org.kde.kirigami as Kirigami

Item {
    id: root

    property bool isShown: true
    property bool takesSpace: true
    property int edge: Qt.TopEdge
    property real contentSize: 0

    readonly property bool isTop: edge === Qt.TopEdge
    readonly property bool isHovered: hover.hovered
    readonly property real slideOffset: isShown ? 0 : -contentSize

    default property alias data: holder.data

    function containsActiveFocus() {
        let item = Window.window ? Window.window.activeFocusItem : null
        while (item && item !== holder)
            item = item.parent
        return item === holder
    }

    height: isTop ? (takesSpace ? contentSize : 0) : 0

    Item {
        id: holder
        z: 100
        x: root.isTop ? 0 : root.slideOffset
        y: root.isTop ? root.slideOffset : 0
        width: root.isTop ? root.width : root.contentSize
        height: root.isTop ? root.contentSize : root.height
        visible: root.slideOffset > -root.contentSize || root.isShown

        Behavior on x { enabled: !root.takesSpace; NumberAnimation { duration: Kirigami.Units.shortDuration } }
        Behavior on y { enabled: !root.takesSpace; NumberAnimation { duration: Kirigami.Units.shortDuration } }

        HoverHandler { id: hover }
    }
}
