// #5 Find in page — find bar (InlineBar) between the header and the page.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    address: "https://pt.wikipedia.org/wiki/KDE"
    tabs: [{ title: "KDE – Wikipedia, the free encyclopedia", icon: "internet-web-browser" }]

    belowHeader: [
        // InlineBar: strip with View colors and thin separators.
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: findRow.implicitHeight + 2 * Kirigami.Units.smallSpacing
            Kirigami.Theme.colorSet: Kirigami.Theme.View
            Kirigami.Theme.inherit: false
            color: Kirigami.Theme.backgroundColor
            Kirigami.Separator { anchors { left: parent.left; right: parent.right; top: parent.top } }
            Kirigami.Separator { anchors { left: parent.left; right: parent.right; bottom: parent.bottom } }

            RowLayout {
                id: findRow
                anchors { fill: parent; leftMargin: Kirigami.Units.largeSpacing; rightMargin: Kirigami.Units.smallSpacing }
                spacing: Kirigami.Units.smallSpacing

                Kirigami.Icon { source: "edit-find"; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
                TextField {
                    Layout.preferredWidth: 280
                    text: "Plasma"
                    placeholderText: "Find in page"
                    focus: true
                }
                ToolButton { icon.name: "go-up"; display: AbstractButton.IconOnly; ToolTip.text: "Previous (Shift+F3)" }
                ToolButton { icon.name: "go-down"; display: AbstractButton.IconOnly; ToolTip.text: "Next (F3)" }
                Label { text: "3 of 12"; color: Kirigami.Theme.disabledTextColor; Layout.leftMargin: 6 }
                CheckBox { text: "Match case"; Layout.leftMargin: 12 }
                Item { Layout.fillWidth: true }
                ToolButton { icon.name: "window-close"; display: AbstractButton.IconOnly; ToolTip.text: "Close (Esc)" }
            }
        }
    ]

    FakePage {
        heading: "KDE <mark>Plasma</mark>"
        paragraphs: [
            "<mark>Plasma</mark> is the desktop environment made by the KDE community. It is light, fast and fully configurable, from panels to keyboard shortcuts.",
            "With <cur>Plasma</cur> 6, the whole stack moved to Qt 6 and KDE Frameworks 6, bringing Wayland as the default session, HDR and accessibility improvements."
        ]
    }
}
