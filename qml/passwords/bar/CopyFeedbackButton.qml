import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami

ToolButton {
    id: root

    required property string iconName
    required property string tooltipText
    required property string copiedTooltipText
    required property string announcement
    required property string accessibleName

    property bool isCopied: false

    signal copyRequested()

    function copy() {
        copyRequested()
        isCopied = true
        resetTimer.restart()
        Accessible.announce(announcement)
    }

    display: AbstractButton.IconOnly
    icon.name: isCopied ? "dialog-ok-apply" : iconName
    icon.color: isCopied ? Kirigami.Theme.positiveTextColor : "transparent"
    icon.width: Kirigami.Units.iconSizes.smallMedium
    icon.height: Kirigami.Units.iconSizes.smallMedium
    ToolTip.visible: hovered
    ToolTip.text: isCopied ? copiedTooltipText : tooltipText
    ToolTip.delay: 600
    Accessible.name: accessibleName
    onClicked: copy()

    Timer {
        id: resetTimer
        interval: 2000
        onTriggered: root.isCopied = false
    }
}
