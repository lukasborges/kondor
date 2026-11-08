// #23 Spell checking — underlined word in a text field and suggestions at the top of the context menu.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    address: "https://invent.kde.org/lukasborges/kondor/-/issues/23"
    tabs: [{ title: "Spell checking (#23) · Kondor", icon: "kde" }]
    Rectangle {
        anchors.fill: parent
        color: "#ffffff"
        ColumnLayout {
            x: 80; y: 40
            width: 640
            spacing: 10
            Text { text: "Comment"; font.pixelSize: 18; font.bold: true; color: "#232629" }
            Rectangle {
                Layout.fillWidth: true; height: 150; radius: 4; border.color: "#3daee9"; color: "#fcfcfc"
                Text {
                    x: 12; y: 12; width: parent.width - 24
                    wrapMode: Text.WordWrap; font.pixelSize: 15; color: "#232629"; textFormat: Text.RichText
                    text: "I tested spell checking and it works really well in the <span style='color:#232629'>browswer</span>. Both the English and Portuguese dictionaries were loaded."
                }
                // Simulated wavy underline
                Canvas {
                    x: 386; y: 32; width: 66; height: 5
                    onPaint: { const c = getContext("2d"); c.strokeStyle = "#da4453"; c.lineWidth = 1.2; c.beginPath()
                        for (let i = 0; i <= width; i += 3) c.lineTo(i, (i / 3) % 2 ? 4 : 1); c.stroke() }
                }
            }
        }
    }

    Menu {
        popupType: Popup.Item
        x: 560
        y: 96
        MenuItem { text: "browser"; font.bold: true }
        MenuItem { text: "browsers"; font.bold: true }
        MenuItem { text: "brewer"; font.bold: true }
        MenuSeparator {}
        MenuItem { text: "Undo"; icon.name: "edit-undo" }
        MenuItem { text: "Cut"; icon.name: "edit-cut" }
        MenuItem { text: "Copy"; icon.name: "edit-copy" }
        MenuItem { text: "Paste"; icon.name: "edit-paste" }
        MenuItem { text: "Select All"; icon.name: "edit-select-all" }
        MenuSeparator {}
        Menu {
            title: "Spell Check Languages"
            icon.name: "tools-check-spelling"
            popupType: Popup.Item
            MenuItem { text: "Português (Brasil)"; checkable: true; checked: true }
            MenuItem { text: "English (US)"; checkable: true; checked: true }
        }
        Component.onCompleted: open()
    }
}
