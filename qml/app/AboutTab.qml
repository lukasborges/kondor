import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ColumnLayout {
    id: root
    spacing: Kirigami.Units.largeSpacing

    signal linkActivated(string url)
    signal licenseRequested

    Label {
        text: qsTr("Web Browser")
    }
    Label {
        text: qsTr("© 2026 The Kondor Developers")
    }
    Label {
        Layout.fillWidth: true
        textFormat: Text.RichText
        linkColor: Kirigami.Theme.linkColor
        text: "<a href=\"https://github.com/lukasborges/kondor\">https://github.com/lukasborges/kondor</a>"
        onLinkActivated: function(link) {
            root.linkActivated(link)
        }
    }
    Label {
        Layout.fillWidth: true
        textFormat: Text.RichText
        linkColor: Kirigami.Theme.linkColor
        text: "<a href=\"#license\">" + qsTr("License: GNU General Public License Version 3") + "</a>"
        onLinkActivated: function(link) {
            if (link === "#license")
                root.licenseRequested()
        }
    }

    Item { Layout.fillHeight: true }
}
