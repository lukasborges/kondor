import QtQuick
import org.kde.kirigami as Kirigami

Item {
    id: card

    property bool isBelowAddressBar: false
    property bool isActive: false
    property bool isHovered: false
    property bool hasKeyboardFocus: false

    readonly property color fillColor: isActive ? activeFillColor
        : isHovered ? Qt.alpha(Kirigami.Theme.textColor, 0.05) : "transparent"
    readonly property color activeFillColor: isBelowAddressBar
        ? Qt.alpha(Kirigami.Theme.highlightColor, 0.2) : toolBarColors.backgroundColor
    readonly property color activeBorderColor: isBelowAddressBar
        ? Kirigami.Theme.highlightColor : Qt.alpha(Kirigami.Theme.textColor, 0.2)
    readonly property color borderColor: hasKeyboardFocus ? Kirigami.Theme.focusColor
        : isActive ? activeBorderColor : "transparent"

    Item {
        id: toolBarColors
        Kirigami.Theme.colorSet: Kirigami.Theme.Window
        Kirigami.Theme.inherit: false
        readonly property color backgroundColor: Kirigami.Theme.backgroundColor
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 1
        radius: Kirigami.Units.cornerRadius
        color: card.fillColor
        border.color: card.borderColor
        border.width: 1
    }
}
