import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ItemDelegate {
    id: root

    required property var item
    required property string extensionId
    required property var tab

    Layout.fillWidth: true
    padding: Kirigami.Units.smallSpacing
    text: item.title
    Accessible.description: item.shortcut ?? ""
    onClicked: tab.extensionItems.trigger(extensionId, item.id, false)
    Keys.onReturnPressed: clicked()
    Keys.onEnterPressed: clicked()

    contentItem: RowLayout {
        spacing: Kirigami.Units.smallSpacing

        Kirigami.Icon {
            source: root.item.icon ?? ""
            Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
            Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
        }

        Label {
            text: root.text
            elide: Text.ElideRight
            Layout.fillWidth: true
        }

        Label {
            text: root.item.shortcut ?? ""
            color: Kirigami.Theme.disabledTextColor
            visible: text !== ""
        }
    }
}
