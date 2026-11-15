import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami

TextField {
    id: root

    signal stepDownRequested()
    signal openRequested(bool background)

    function isBackgroundKey(event) {
        return (event.modifiers & Qt.ControlModifier) !== 0
    }

    leftPadding: Kirigami.Units.iconSizes.small + Kirigami.Units.largeSpacing
    Accessible.name: placeholderText
    Keys.onDownPressed: stepDownRequested()
    Keys.onReturnPressed: function(event) { openRequested(isBackgroundKey(event)) }
    Keys.onEnterPressed: function(event) { openRequested(isBackgroundKey(event)) }

    Kirigami.Icon {
        source: "edit-find"
        x: Kirigami.Units.smallSpacing
        width: Kirigami.Units.iconSizes.small
        height: Kirigami.Units.iconSizes.small
        anchors.verticalCenter: parent.verticalCenter
    }
}
