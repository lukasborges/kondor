// #183 Extensions panel — level 2: the actions of one extension, with Back, pin and settings.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    address: "https://www.youtube.com/watch?v=example"
    toolbarExtras: [
        ToolButton { display: AbstractButton.IconOnly; icon.name: "media-playback-start" },
        ToolButton { display: AbstractButton.IconOnly; icon.name: "plugins"; checked: true }
    ]
    FakePage {}

    component ActionRow: ItemDelegate {
        id: action
        property string shortcut: ""
        Layout.fillWidth: true
        padding: Kirigami.Units.smallSpacing
        contentItem: RowLayout {
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Icon {
                source: action.icon.name
                Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
            }
            Label { text: action.text; Layout.fillWidth: true }
            Label { text: action.shortcut; color: Kirigami.Theme.disabledTextColor }
        }
    }

    ExtensionsPanelMock {
        x: frame.width - width - 44
        y: -6
        showList: false

        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing
            ToolButton { icon.name: "go-previous"; display: AbstractButton.IconOnly; Accessible.name: "Back to Extensions" }
            Kirigami.Icon {
                source: "media-playback-start"
                Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
            }
            Kirigami.Heading { level: 4; text: "Video Speed Controller"; elide: Text.ElideRight; Layout.fillWidth: true }
        }
        Kirigami.Separator { Layout.fillWidth: true }
        ActionRow { text: "Slower"; icon.name: "media-seek-backward"; shortcut: "S" }
        ActionRow { text: "Faster"; icon.name: "media-seek-forward"; shortcut: "D" }
        ActionRow { text: "Reset Speed"; icon.name: "edit-undo"; shortcut: "R" }
        CheckBox { text: "Show speed overlay"; checked: true; Layout.leftMargin: Kirigami.Units.smallSpacing }
        Kirigami.Separator { Layout.fillWidth: true }
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: Kirigami.Units.smallSpacing
            Label { text: "Run on www.youtube.com"; Layout.fillWidth: true }
            Switch { checked: true; Accessible.name: "Run Video Speed Controller on www.youtube.com" }
        }
        Kirigami.Separator { Layout.fillWidth: true }
        RowLayout {
            Layout.fillWidth: true
            Button { text: "Unpin from Toolbar"; icon.name: "window-unpin"; flat: true }
            Item { Layout.fillWidth: true }
            Button { text: "Settings…"; icon.name: "configure"; flat: true }
        }
    }
}
