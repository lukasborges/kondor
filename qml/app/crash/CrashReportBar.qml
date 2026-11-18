import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Kirigami.InlineMessage {
    id: root

    property bool isEligible: true

    signal reportRequested(url address)

    Layout.fillWidth: true
    position: Kirigami.InlineMessage.Position.Header
    type: Kirigami.MessageType.Warning
    showCloseButton: true
    visible: false
    text: qsTr("Kondor closed unexpectedly.")

    actions: [
        Kirigami.Action {
            text: qsTr("Report Problem…")
            icon.name: "tools-report-bug"
            onTriggered: {
                const address = CrashReporter.report()
                root.visible = false
                root.reportRequested(address)
            }
        }
    ]

    onVisibleChanged: {
        if (!visible)
            CrashReporter.dismiss()
    }

    Component.onCompleted: visible = isEligible && CrashReporter.claimBar()
}
