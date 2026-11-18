import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami

AbstractButton {
    id: swatch

    property string colorName: "blue"

    implicitWidth: Kirigami.Units.gridUnit * 1.5
    implicitHeight: implicitWidth
    checkable: true
    autoExclusive: true
    ToolTip.visible: hovered
    ToolTip.text: text
    ToolTip.delay: 600
    Accessible.name: text

    GroupColor {
        id: tint
        name: swatch.colorName
    }

    contentItem: Rectangle {
        radius: width / 2
        color: tint.value
        border.width: swatch.visualFocus ? 2 : swatch.checked ? 2 : 0
        border.color: swatch.visualFocus ? Kirigami.Theme.focusColor : Kirigami.Theme.textColor

        Kirigami.Icon {
            visible: swatch.checked
            anchors.centerIn: parent
            width: 14
            height: 14
            source: "checkmark"
            color: Kirigami.Theme.highlightedTextColor
            isMask: true
        }
    }
}
