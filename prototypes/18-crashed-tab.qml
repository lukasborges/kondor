// #18 Crashed page — page overlaid when the render process dies.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    tabs: [{ title: "KDE Community", icon: "dialog-error" }, { title: "Planet KDE", icon: "internet-web-browser" }]
    Rectangle {
        anchors.fill: parent
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor
        ColumnLayout {
            anchors.centerIn: parent
            width: 480
            spacing: Kirigami.Units.largeSpacing * 2
            Kirigami.Icon { source: "dialog-error"; Layout.preferredWidth: 64; Layout.preferredHeight: 64; Layout.alignment: Qt.AlignHCenter }
            Kirigami.Heading { level: 2; text: "This tab crashed"; Layout.alignment: Qt.AlignHCenter }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                text: "The page's process was terminated, possibly because the system ran out of memory. Other tabs were not affected."
            }
            Label { text: "Exit code: 9"; color: Kirigami.Theme.disabledTextColor; font: Kirigami.Theme.smallFont; Layout.alignment: Qt.AlignHCenter }
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: Kirigami.Units.largeSpacing
                Button { text: "Close Tab"; icon.name: "tab-close" }
                Button { text: "Reload"; icon.name: "view-refresh"; highlighted: true }
            }
        }
    }
}
