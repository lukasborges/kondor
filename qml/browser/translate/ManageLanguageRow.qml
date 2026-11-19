import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

RowLayout {
    id: root

    required property var modelData

    Kirigami.Icon {
        source: "languages"
        implicitWidth: Kirigami.Units.iconSizes.smallMedium
        implicitHeight: implicitWidth
    }

    Label {
        Layout.fillWidth: true
        text: root.modelData.label
    }

    Label {
        text: qsTr("%1 MB").arg(root.modelData.megabytes)
        color: Kirigami.Theme.disabledTextColor
    }

    ToolButton {
        icon.name: "edit-delete"
        display: AbstractButton.IconOnly
        ToolTip.visible: hovered
        ToolTip.text: qsTr("Remove")
        ToolTip.delay: 600
        Accessible.name: qsTr("Remove %1").arg(root.modelData.label)
        onClicked: TranslationLibrary.remove(root.modelData.source, root.modelData.target)
    }
}
