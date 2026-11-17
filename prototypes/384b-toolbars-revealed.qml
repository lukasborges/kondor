// #384 With the toolbars hidden, the pointer at the top edge (or Ctrl+L) slides tab strip and
// toolbar in over the page; they hide again when the pointer leaves and nothing in them has focus.
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import "common"

Rectangle {
    width: 1100
    height: 700
    color: Kirigami.Theme.backgroundColor

    BrowserFrame {
        anchors.fill: parent
        showHeader: false
        FakePage {}
    }

    BrowserFrame {
        id: header
        width: parent.width
        height: 92
        tabs: [
            { title: "KDE Community", icon: "kde" },
            { title: "Wikipedia, the free encyclopedia", icon: "internet-web-browser" }
        ]
        Item {}
    }

    Rectangle {
        anchors.top: header.bottom
        width: parent.width
        height: Kirigami.Units.smallSpacing
        gradient: Gradient {
            GradientStop { position: 0; color: Qt.rgba(0, 0, 0, 0.18) }
            GradientStop { position: 1; color: "transparent" }
        }
    }
}
