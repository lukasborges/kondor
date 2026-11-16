import QtQuick
import QtQuick.Controls

QtObject {
    id: root

    required property Menu menu

    function isUsable(item) {
        return item && item.highlighted !== undefined && item.enabled && item.visible
    }

    function usableIndexFrom(start, delta) {
        for (let step = 1; step <= root.menu.count; step++) {
            const index = (start + delta * step + root.menu.count * 2) % root.menu.count
            if (root.isUsable(root.menu.itemAt(index)))
                return index
        }
        return root.menu.currentIndex
    }

    function move(delta) {
        const start = root.menu.currentIndex < 0 && delta < 0 ? 0 : root.menu.currentIndex
        root.menu.currentIndex = root.usableIndexFrom(start, delta)
    }

    property list<Shortcut> shortcuts: [
        Shortcut {
            sequence: "Down"
            enabled: root.menu.activeFocus
            onActivated: root.move(1)
        },
        Shortcut {
            sequence: "Up"
            enabled: root.menu.activeFocus
            onActivated: root.move(-1)
        }
    ]
}
