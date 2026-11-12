import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kondor

Dialog {
    id: root
    title: qsTr("Clear History")
    standardButtons: Dialog.Ok | Dialog.Cancel
    modal: true
    anchors.centerIn: parent

    function startOfToday() {
        const date = new Date()
        date.setHours(0, 0, 0, 0)
        return date.getTime()
    }

    function clearSelectedRange() {
        const clearActions = [
            function() { HistoryManager.clearSince(Date.now() - 3600 * 1000) },
            function() { HistoryManager.clearSince(root.startOfToday()) },
            function() { HistoryManager.clearAll() }
        ]
        clearActions[rangeBox.currentIndex]()
    }

    ColumnLayout {
        spacing: 8

        Label {
            text: qsTr("Remove from history:")
        }

        ComboBox {
            id: rangeBox
            model: [qsTr("Last hour"), qsTr("Today"), qsTr("Everything")]
        }
    }

    onAccepted: clearSelectedRange()
}
