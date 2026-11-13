import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami

ToolButton {
    id: root

    required property var modelData

    display: AbstractButton.IconOnly
    ToolTip.visible: hovered
    ToolTip.text: modelData.name
    ToolTip.delay: 600
    Accessible.name: modelData.name

    contentItem: Kirigami.Icon {
        source: root.modelData.iconSource
        implicitWidth: Kirigami.Units.iconSizes.smallMedium
        implicitHeight: Kirigami.Units.iconSizes.smallMedium
    }
}
