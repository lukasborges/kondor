// #44 Address bar: visit or search — the typed text looks like an address, so the dropdown
// offers "Visit" (selected, what Enter does) and "Search with <engine>".
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    address: "teste.com.br"
    addressFocused: true
    Component.onCompleted: { addressField.forceActiveFocus(); addressField.cursorPosition = 12 }
    FakePage {}

    Popup {
        popupType: Popup.Item
        x: frame.addressField.x
        y: -6
        width: frame.addressField.width
        padding: 0
        Component.onCompleted: open()
        contentItem: ColumnLayout {
            spacing: 0
            Repeater {
                model: [
                    { i: "globe", t: "https://teste.com.br", s: "Visit", sel: true },
                    { i: "edit-find", t: "teste.com.br", s: "Search with DuckDuckGo", sel: false }
                ]
                delegate: ItemDelegate {
                    id: row
                    required property var modelData
                    Layout.fillWidth: true
                    highlighted: modelData.sel
                    contentItem: RowLayout {
                        spacing: Kirigami.Units.largeSpacing
                        Kirigami.Icon { source: row.modelData.i; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
                        Label { text: row.modelData.t; elide: Text.ElideRight; Layout.maximumWidth: 420 }
                        Label {
                            text: "— " + row.modelData.s
                            color: row.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.disabledTextColor
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }
    }
}
