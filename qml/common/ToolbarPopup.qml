import QtQuick
import QtQuick.Controls

Popup {
    id: root

    property Item itemFocusedBeforeOpening: null

    readonly property Window hostWindow: parent.Window.window

    function hasFocusBeenTaken() {
        return hostWindow.activeFocusItem !== hostWindow.contentItem
    }

    function restoreFocus() {
        if (itemFocusedBeforeOpening && !hasFocusBeenTaken())
            itemFocusedBeforeOpening.forceActiveFocus()
        itemFocusedBeforeOpening = null
    }

    modal: false
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    onAboutToShow: itemFocusedBeforeOpening = hostWindow.activeFocusItem
    onClosed: restoreFocus()
}
