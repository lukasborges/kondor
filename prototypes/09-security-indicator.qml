// #9 Security indicator — cadeado na barra de endereço e popup de informações do site.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; checked: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    FakePage {}

    Popup {
        popupType: Popup.Item
        x: 166
        y: -4
        width: 360
        padding: Kirigami.Units.largeSpacing
        Component.onCompleted: open()
        contentItem: ColumnLayout {
            spacing: Kirigami.Units.largeSpacing
            RowLayout {
                spacing: Kirigami.Units.largeSpacing
                Kirigami.Icon { source: "security-high"; Layout.preferredWidth: 32; Layout.preferredHeight: 32 }
                ColumnLayout {
                    spacing: 0
                    Kirigami.Heading { level: 4; text: "kde.org" }
                    Label { text: "A conexão com este site é segura"; color: Kirigami.Theme.positiveTextColor }
                }
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: Kirigami.Theme.disabledTextColor
                text: "Certificado emitido por Let's Encrypt (R11), válido até 12/02/2027."
            }
            Kirigami.Separator { Layout.fillWidth: true }
            Label { text: "Permissões deste site"; font.bold: true }
            RowLayout {
                Kirigami.Icon { source: "preferences-desktop-notification"; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
                Label { text: "Notificações"; Layout.fillWidth: true }
                Label { text: "Permitido"; color: Kirigami.Theme.positiveTextColor }
                ToolButton { icon.name: "edit-undo"; display: AbstractButton.IconOnly }
            }
            Button { text: "Limpar cookies e dados do site"; icon.name: "edit-clear"; flat: true }
        }
    }
}
