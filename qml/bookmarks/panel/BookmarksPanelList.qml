import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: root

    required property var entries
    required property string emptyText

    signal entryOpened(var entry, bool background)
    signal topReached()

    function focusRow(index) {
        const target = Math.max(0, Math.min(index, list.count - 1))
        list.positionViewAtIndex(target, ListView.Contain)
        list.currentIndex = target
        const row = list.itemAtIndex(target)
        if (row)
            row.forceActiveFocus()
    }

    function openCurrent(background) {
        if (list.currentIndex >= 0 && list.currentIndex < entries.length)
            entryOpened(entries[list.currentIndex], background)
    }

    function stepFrom(index, step) {
        if (index + step < 0)
            topReached()
        else
            focusRow(index + step)
    }

    spacing: 0

    ScrollView {
        visible: root.entries.length > 0
        Layout.fillWidth: true
        Layout.preferredHeight: Math.min(list.contentHeight, Kirigami.Units.gridUnit * 24)

        ListView {
            id: list
            objectName: "bookmarksPanelList"
            model: root.entries
            clip: true
            onModelChanged: currentIndex = count > 0 ? 0 : -1

            section.property: "section"
            section.delegate: Kirigami.ListSectionHeader {
                required property string section
                text: section
                visible: section !== ""
                height: visible ? implicitHeight : 0
                width: ListView.view.width
            }

            delegate: BookmarksPanelEntry {
                onOpenRequested: function(background) { root.entryOpened(modelData, background) }
                onStepRequested: function(step) { root.stepFrom(index, step) }
            }
        }
    }

    Label {
        visible: root.entries.length === 0
        text: root.emptyText
        color: Kirigami.Theme.disabledTextColor
        horizontalAlignment: Text.AlignHCenter
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.largeSpacing
    }
}
