// The suggested password popup under a new-password field (#260): one row, no password shown.
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami

Popup {
    id: popup

    property bool rowHighlighted: false

    popupType: Popup.Item
    padding: Kirigami.Units.smallSpacing
    focus: false
    closePolicy: Popup.CloseOnPressOutside

    ItemDelegate {
        implicitWidth: Math.max(popup.width - popup.leftPadding - popup.rightPadding, implicitContentWidth + leftPadding + rightPadding)
        focusPolicy: Qt.NoFocus
        highlighted: popup.rowHighlighted
        text: "Use Suggested Password"
        icon.name: "password-generate"
        ToolTip.visible: popup.rowHighlighted
        ToolTip.delay: 600
        ToolTip.text: "Fill in a strong password and save it in KWallet when the form is sent"
    }

    Component.onCompleted: open()
}
