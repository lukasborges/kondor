import QtQuick

Shortcut {
    required property Window window

    enabled: window.visible && window.activeFocusItem !== null
}
