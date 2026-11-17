import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ItemDelegate {
    id: root

    property string url: ""

    ToolTip.visible: hovered
    ToolTip.text: url
    ToolTip.delay: 600
    Keys.onReturnPressed: clicked()
    Keys.onEnterPressed: clicked()

    contentItem: RowLayout {
        spacing: Kirigami.Units.smallSpacing

        Kirigami.Icon {
            source: "window-new"
            Layout.preferredWidth: Kirigami.Units.iconSizes.small
            Layout.preferredHeight: Kirigami.Units.iconSizes.small
        }

        Label {
            Layout.fillWidth: true
            text: root.text
            elide: Text.ElideMiddle
        }
    }
}
