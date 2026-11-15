import QtQuick
import Kondor

DropArea {
    id: root

    required property BookmarksBarDropTargets targets

    function linkOf(drop) {
        const text = drop.hasText ? drop.text.trim() : ""
        const url = drop.hasUrls ? drop.urls[0].toString() : text
        if (!/^[a-z][a-z0-9+.-]*:[/][/]/i.test(url))
            return null
        return { url: url, title: text.length > 0 && text !== url ? text : url }
    }

    function updateDrop(x) {
        root.targets.dropAtPosition(root.targets.itemUnder(x))
    }

    keys: ["text/uri-list", "text/plain"]
    onEntered: function(drag) {
        drag.accepted = root.linkOf(drag) !== null
        if (drag.accepted)
            root.updateDrop(drag.x)
    }
    onPositionChanged: function(drag) { root.updateDrop(drag.x) }
    onExited: root.targets.drag.clearDropTarget()
    onDropped: function(drop) {
        const link = root.linkOf(drop)
        if (link)
            root.targets.completeLinkDrop(link)
    }
}
