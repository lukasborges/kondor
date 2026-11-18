// #410 Page capture: Take Screenshot… (Ctrl+Shift+S) captures the visible area right away and
// shows it; Full Page captures the whole page instead. Copy puts the image on the clipboard,
// Save… asks where to save the PNG.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    FakePage { id: page }

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.3)
    }

    Dialog {
        popupType: Popup.Item
        modal: true
        anchors.centerIn: parent
        width: Kirigami.Units.gridUnit * 30
        title: "Take Screenshot"
        Component.onCompleted: open()

        contentItem: ColumnLayout {
            spacing: Kirigami.Units.largeSpacing
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 0
                Button { text: "Visible Area"; icon.name: "select-rectangular"; checkable: true; checked: true; autoExclusive: true }
                Button { text: "Full Page"; icon.name: "zoom-fit-page"; checkable: true; autoExclusive: true }
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: width * 0.55
                color: Kirigami.Theme.backgroundColor
                border.color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, Kirigami.Theme.frameContrast)
                clip: true
                ShaderEffectSource {
                    anchors.fill: parent
                    anchors.margins: 1
                    sourceItem: page
                    sourceRect: Qt.rect(0, 0, page.width, page.width * 0.55)
                }
            }
            Label {
                Layout.alignment: Qt.AlignHCenter
                text: "1100 × 616"
                color: Kirigami.Theme.disabledTextColor
            }
        }

        footer: DialogButtonBox {
            Button { text: "Copy"; icon.name: "edit-copy"; DialogButtonBox.buttonRole: DialogButtonBox.ActionRole }
            Button { text: "Save…"; icon.name: "document-save"; highlighted: true; DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole }
            Button { text: "Close"; icon.name: "dialog-close"; DialogButtonBox.buttonRole: DialogButtonBox.RejectRole }
        }
    }
}
