// #11 Address bar suggestions — inline completion ("kd" → "kde.org") and suggestion list.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    address: "kde.org"
    addressFocused: true
    Component.onCompleted: { addressField.forceActiveFocus(); addressField.select(2, 7) }
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
                    { i: "globe", t: "https://kde.org", u: "", s: "Visit", sel: true },
                    { i: "edit-find", t: "kde.org", u: "", s: "Search with DuckDuckGo", sel: false },
                    { i: "bookmarks", t: "KDE Community", u: "https://kde.org/", sel: false },
                    { i: "bookmarks", t: "KDE Human Interface Guidelines", u: "https://develop.kde.org/hig/", sel: false },
                    { i: "view-history", t: "KDE Plasma 6.5 — Release notes", u: "https://kde.org/announcements/plasma/6/6.5.0/", sel: false },
                    { i: "view-history", t: "KDE Applications", u: "https://apps.kde.org/", sel: false },
                    { i: "edit-find", t: "kde connect", u: "", sel: false },
                    { i: "edit-find", t: "kde plasma 6", u: "", sel: false }
                ]
                delegate: ItemDelegate {
                    required property var modelData
                    Layout.fillWidth: true
                    highlighted: modelData.sel
                    contentItem: RowLayout {
                        spacing: Kirigami.Units.largeSpacing
                        Kirigami.Icon { source: modelData.i; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
                        Label { text: modelData.t; elide: Text.ElideRight; Layout.maximumWidth: 420 }
                        Label {
                            visible: modelData.u !== ""
                            text: "— " + modelData.u
                            color: highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.disabledTextColor
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Label {
                            visible: modelData.u === "" && modelData.s !== undefined
                            text: "— " + (modelData.s || "")
                            color: highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.disabledTextColor
                            Layout.fillWidth: true
                        }
                        Item { visible: modelData.u === "" && modelData.s === undefined; Layout.fillWidth: true }
                    }
                }
            }
        }
    }
}
