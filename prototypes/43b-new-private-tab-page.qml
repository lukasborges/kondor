// #43 New Tab page — private variant: no top sites, an explanation of private tabs instead.
// Same look as the private new-tab page of #14 (14-private-window.qml), worded per tab.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    tabs: [{ title: "KDE Community", icon: "kde" }, { title: "New Private Tab", private: true }]
    currentTab: 1
    address: ""
    addressFocused: true

    Rectangle {
        anchors.fill: parent
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor

        ColumnLayout {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: Kirigami.Units.gridUnit * 4
            width: Math.min(parent.width - Kirigami.Units.gridUnit * 4, Kirigami.Units.gridUnit * 30)
            spacing: Kirigami.Units.gridUnit * 2

            Kirigami.Icon { source: "view-private"; Layout.preferredWidth: 96; Layout.preferredHeight: 96; Layout.alignment: Qt.AlignHCenter }
            Kirigami.Heading { level: 1; text: "Private Tab"; Layout.alignment: Qt.AlignHCenter }

            TextField {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: Kirigami.Units.gridUnit * 30
                placeholderText: "Search or enter address"
            }

            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                text: "Kondor Browser does not keep the history, cookies, form data or permissions of this tab. Everything is erased when you close it."
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
