import QtQuick
import org.kde.kirigami as Kirigami

Item {
    id: card

    property bool isActive: false
    property bool isHovered: false
    property bool hasKeyboardFocus: false
    property bool isRaised: false
    property color underlayColor: "transparent"

    readonly property color fillColor: isActive ? Qt.alpha(Kirigami.Theme.highlightColor, 0.2)
        : isHovered ? Qt.alpha(Kirigami.Theme.textColor, 0.05) : "transparent"
    readonly property color borderColor: hasKeyboardFocus ? Kirigami.Theme.focusColor
        : isActive ? Kirigami.Theme.highlightColor : "transparent"

    Rectangle {
        anchors.fill: parent
        anchors.margins: 1
        radius: Kirigami.Units.cornerRadius
        color: card.underlayColor
        visible: card.isRaised
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
