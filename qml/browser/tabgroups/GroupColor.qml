import QtQuick
import org.kde.kirigami as Kirigami

Item {
    id: root

    property string name: "blue"

    readonly property var schemeColors: ({
        blue: Kirigami.Theme.highlightColor,
        green: Kirigami.Theme.positiveTextColor,
        orange: Kirigami.Theme.neutralTextColor,
        red: Kirigami.Theme.negativeTextColor,
        purple: Kirigami.Theme.visitedLinkColor,
        gray: Kirigami.Theme.disabledTextColor
    })
    readonly property color value: schemeColors[name] ?? Kirigami.Theme.highlightColor

    visible: false
    width: 0
    height: 0
}
