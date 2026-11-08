// Generic fake web page used as content in the prototypes.
// heading/paragraphs accept rich text: <mark>word</mark> renders a search highlight
// and <cur>word</cur> the current match highlight.
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    id: page
    property string heading: "Plasma 6: the KDE community desktop"
    property var paragraphs: [
        "Plasma is the desktop environment made by the KDE community. It is light, fast and fully configurable, from panels to keyboard shortcuts.",
        "With Plasma 6, the whole stack moved to Qt 6 and KDE Frameworks 6, bringing Wayland as the default session, HDR and accessibility improvements."
    ]
    property var paragraphsAfter: [
        "Apps like Dolphin, Konsole, Kate and Okular follow the same Human Interface Guidelines and the Breeze theme, for a consistent experience."
    ]
    property bool showHero: true
    anchors.fill: parent
    color: "#ffffff"

    function rich(s) {
        return s.replace(/<mark>/g, "<span style='background-color:#fdbc4b'>")
                .replace(/<cur>/g, "<span style='background-color:#f67400;color:#ffffff'>")
                .replace(/<\/(mark|cur)>/g, "</span>")
    }

    Rectangle {
        id: siteHeader
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: 56
        color: "#232629"
        Row {
            anchors.verticalCenter: parent.verticalCenter
            x: 40
            spacing: 28
            Kirigami.Icon { source: "kde"; width: 28; height: 28; anchors.verticalCenter: parent.verticalCenter }
            Repeater {
                model: ["Products", "Community", "Donate", "News"]
                Text { text: modelData; color: "#fcfcfc"; font.pixelSize: 14; anchors.verticalCenter: parent.verticalCenter }
            }
        }
    }

    ColumnLayout {
        anchors { left: parent.left; top: siteHeader.bottom; leftMargin: 80; topMargin: 32 }
        width: Math.min(640, page.width - 160)
        spacing: 14
        Text {
            Layout.fillWidth: true
            text: page.rich(page.heading)
            textFormat: Text.RichText
            font.pixelSize: 30; font.bold: true; color: "#232629"
            wrapMode: Text.WordWrap
        }
        Repeater {
            model: page.paragraphs
            Text {
                Layout.fillWidth: true
                text: page.rich(modelData)
                textFormat: Text.RichText
                font.pixelSize: 15; color: "#31363b"; lineHeight: 1.35
                wrapMode: Text.WordWrap
            }
        }
        Rectangle {
            visible: page.showHero
            Layout.fillWidth: true
            Layout.preferredHeight: 150
            radius: 6
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: "#3daee9" }
                GradientStop { position: 1; color: "#1d78b5" }
            }
            Kirigami.Icon { anchors.centerIn: parent; source: "plasma"; width: 64; height: 64 }
        }
        Repeater {
            model: page.paragraphsAfter
            Text {
                Layout.fillWidth: true
                text: page.rich(modelData)
                textFormat: Text.RichText
                font.pixelSize: 15; color: "#31363b"; lineHeight: 1.35
                wrapMode: Text.WordWrap
            }
        }
    }
}
