import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ToolbarPopup {
    id: root

    required property TabTranslation translation

    signal manageRequested()

    readonly property string state: translation.state

    width: 360
    padding: Kirigami.Units.largeSpacing

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        RowLayout {
            Kirigami.Heading {
                Layout.fillWidth: true
                level: 4
                text: root.state === "translated" ? qsTr("Page Translated") : qsTr("Translate Page")
            }

            ToolButton {
                id: moreButton
                icon.name: "overflow-menu"
                display: AbstractButton.IconOnly
                checked: moreMenu.opened
                ToolTip.visible: hovered
                ToolTip.text: qsTr("More Options")
                ToolTip.delay: 600
                Accessible.name: ToolTip.text
                onClicked: moreMenu.opened ? moreMenu.close() : moreMenu.open()
            }
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: root.state === "error"
            type: Kirigami.MessageType.Error
            text: qsTr("Could not download the language files.")
        }

        TranslateLanguageForm {
            Layout.fillWidth: true
            translation: root.translation
            isEditable: root.state !== "downloading"
        }

        TranslateDownloadProgress {
            Layout.fillWidth: true
            visible: root.state === "downloading"
            translation: root.translation
        }

        Label {
            visible: root.state === "translating"
            text: qsTr("Translating…")
            color: Kirigami.Theme.disabledTextColor
        }

        TranslateButtons {
            translation: root.translation
            onDismissed: root.close()
        }
    }

    TranslateMenu {
        id: moreMenu
        translation: root.translation
        x: moreButton.x + moreButton.width - width + root.leftPadding
        y: moreButton.y + moreButton.height + root.topPadding
        onManageRequested: {
            root.close()
            root.manageRequested()
        }
    }
}
