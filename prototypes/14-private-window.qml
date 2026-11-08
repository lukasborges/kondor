// #14 Multiple windows — private window: private browsing icon in the tab bar,
// every tab private and a new-tab page explaining the mode.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    privateWindow: true
    tabs: [{ title: "New Private Tab", private: true }, { title: "Search — DuckDuckGo", private: true }]
    address: ""
    Rectangle {
        anchors.fill: parent
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor
        ColumnLayout {
            anchors.centerIn: parent
            width: 520
            spacing: Kirigami.Units.largeSpacing * 2
            Kirigami.Icon { source: "view-private"; Layout.preferredWidth: 96; Layout.preferredHeight: 96; Layout.alignment: Qt.AlignHCenter }
            Kirigami.Heading { level: 1; text: "Private Browsing"; Layout.alignment: Qt.AlignHCenter }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                text: "Kondor does not keep history, cookies, form data or permissions from this window. Everything is erased when you close it."
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                color: Kirigami.Theme.disabledTextColor
                text: "Downloads and bookmarks you create are kept. Your provider and the sites you visit can still see your activity."
            }
        }
    }
}
