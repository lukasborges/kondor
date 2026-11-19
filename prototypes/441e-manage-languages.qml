// #441 Translate pages on the device: Manage Languages lists the downloaded language files with
// their size; Remove deletes one pair. Nothing else is stored: pages are translated on this computer.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    height: 560
    address: "https://kde.org/"
    FakePage {}

    Dialog {
        popupType: Popup.Item
        anchors.centerIn: parent
        width: 460
        modal: true
        title: "Manage Languages"
        standardButtons: Dialog.Close
        Component.onCompleted: open()
        contentItem: ColumnLayout {
            spacing: Kirigami.Units.smallSpacing
            Repeater {
                model: [
                    { pair: "English → Portuguese", size: "32 MB" },
                    { pair: "Portuguese → English", size: "30 MB" },
                    { pair: "German → English", size: "28 MB" }
                ]
                delegate: RowLayout {
                    required property var modelData
                    Layout.fillWidth: true
                    Kirigami.Icon { source: "languages"; implicitWidth: Kirigami.Units.iconSizes.smallMedium; implicitHeight: implicitWidth }
                    Label { text: modelData.pair; Layout.fillWidth: true }
                    Label { text: modelData.size; color: Kirigami.Theme.disabledTextColor }
                    ToolButton {
                        icon.name: "edit-delete"
                        display: AbstractButton.IconOnly
                        ToolTip.text: "Remove"
                        ToolTip.delay: 600
                        Accessible.name: "Remove " + modelData.pair
                    }
                }
            }
        }
    }
}
