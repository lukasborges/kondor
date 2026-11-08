// #16 Developer tools — DevTools docked below the page (vertical SplitView).
// The bottom part is Chromium DevTools itself (only a visual imitation here).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    SplitView {
        anchors.fill: parent
        orientation: Qt.Vertical
        Item {
            SplitView.fillHeight: true
            clip: true
            FakePage {}
            Rectangle { x: 80; y: 88; width: 560; height: 44; color: "#553daee9"; border.color: "#3daee9" }
        }
        Rectangle {
            SplitView.preferredHeight: 260
            color: "#ffffff"
            ColumnLayout {
                anchors.fill: parent
                spacing: 0
                Rectangle {
                    Layout.fillWidth: true; Layout.preferredHeight: 30; color: "#f1f3f4"
                    Row {
                        anchors.verticalCenter: parent.verticalCenter; x: 10; spacing: 22
                        Repeater {
                            model: ["Elements", "Console", "Sources", "Network", "Performance", "Application"]
                            Text { text: modelData; font.pixelSize: 12; color: index === 0 ? "#1a73e8" : "#3c4043" }
                        }
                    }
                    Text { anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter; text: "✕"; color: "#5f6368" }
                }
                Text {
                    Layout.fillWidth: true; Layout.fillHeight: true; Layout.margins: 10
                    font.family: "monospace"; font.pixelSize: 12; color: "#3c4043"; textFormat: Text.RichText
                    text: "&lt;<span style='color:#881280'>body</span>&gt;<br>&nbsp;&nbsp;&lt;<span style='color:#881280'>header</span> <span style='color:#994500'>class</span>=<span style='color:#1a1aa6'>\"site-header\"</span>&gt;…&lt;/<span style='color:#881280'>header</span>&gt;<br>" +
                          "&nbsp;&nbsp;&lt;<span style='color:#881280'>main</span>&gt;<br>&nbsp;&nbsp;&nbsp;&nbsp;<span style='background-color:#cfe8fc'>&lt;<span style='color:#881280'>h1</span>&gt;Plasma 6: o desktop da comunidade KDE&lt;/<span style='color:#881280'>h1</span>&gt; == $0</span><br>" +
                          "&nbsp;&nbsp;&nbsp;&nbsp;&lt;<span style='color:#881280'>p</span>&gt;…&lt;/<span style='color:#881280'>p</span>&gt;<br>&nbsp;&nbsp;&lt;/<span style='color:#881280'>main</span>&gt;<br>&lt;/<span style='color:#881280'>body</span>&gt;"
                }
            }
        }
    }
}
