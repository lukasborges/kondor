// #403 Crash reports: the first window after Kondor recovers from a crash offers to report it.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    belowHeader: [
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            position: Kirigami.InlineMessage.Position.Header
            visible: true
            type: Kirigami.MessageType.Warning
            showCloseButton: true
            text: "Kondor closed unexpectedly."
            actions: [
                Kirigami.Action { text: "Report Problem…"; icon.name: "tools-report-bug" }
            ]
        }
    ]
    FakePage { heading: "KDE Community" }
}
