// #441 Translate page panel, opened from the address bar's translate button.
// state: "offer" (page not translated), "downloading" (first use of a language pair),
// "translated" (page shown translated).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Popup {
    id: root
    property string state: "offer"
    property bool menuOpen: false
    popupType: Popup.Item
    width: 360
    padding: Kirigami.Units.largeSpacing
    Component.onCompleted: open()

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing
        RowLayout {
            Kirigami.Heading {
                Layout.fillWidth: true
                level: 4
                text: root.state === "translated" ? "Page Translated" : "Translate Page"
            }
            ToolButton {
                id: moreButton
                icon.name: "overflow-menu"
                display: AbstractButton.IconOnly
                checked: root.menuOpen
                ToolTip.text: "More Options"
                ToolTip.delay: 600
                Accessible.name: "More Options"
            }
        }
        Kirigami.FormLayout {
            Layout.fillWidth: true
            ComboBox {
                Kirigami.FormData.label: "From:"
                Layout.fillWidth: true
                model: ["English (detected)", "German", "French", "Spanish"]
                enabled: root.state !== "downloading"
            }
            ComboBox {
                Kirigami.FormData.label: "To:"
                Layout.fillWidth: true
                model: ["Portuguese", "English", "Spanish"]
                enabled: root.state !== "downloading"
            }
        }
        ColumnLayout {
            visible: root.state === "downloading"
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing
            ProgressBar { Layout.fillWidth: true; from: 0; to: 32; value: 12 }
            Label {
                Layout.fillWidth: true
                text: "Downloading English → Portuguese: 12 of 32 MB"
                color: Kirigami.Theme.disabledTextColor
                font: Kirigami.Theme.smallFont
                elide: Text.ElideRight
            }
        }
        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: Kirigami.Units.smallSpacing
            Button {
                visible: root.state === "offer"
                text: "Not Now"
            }
            Button {
                visible: root.state === "downloading"
                text: "Cancel"
                icon.name: "dialog-cancel"
            }
            Button {
                visible: root.state === "translated"
                text: "Show Original"
                icon.name: "edit-undo"
            }
            Button {
                visible: root.state === "offer"
                text: "Translate"
                icon.name: "translate"
                highlighted: true
            }
        }
    }

    Menu {
        id: moreMenu
        popupType: Popup.Item
        x: moreButton.x + moreButton.width - width + root.leftPadding
        y: moreButton.y + moreButton.height + root.topPadding
        Component.onCompleted: if (root.menuOpen) open()
        MenuItem { text: "Always Translate English"; checkable: true }
        MenuItem { text: "Never Translate English"; checkable: true }
        MenuItem { text: "Never Translate kde.org"; checkable: true }
        MenuSeparator {}
        MenuItem { text: "Manage Languages…"; icon.name: "languages" }
    }
}
