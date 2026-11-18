import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ListView {
    id: list

    property bool showsSections: true

    signal tabChosen(var tab)
    signal tabCloseRequested(var tab)

    function isFirstOfWindow(index) {
        return index === 0 || model[index - 1].windowNumber !== model[index].windowNumber
    }

    function selectFirstOtherTab() {
        const first = model.findIndex(entry => !entry.isCurrent)
        currentIndex = first >= 0 ? first : 0
    }

    function moveSelection(delta) {
        currentIndex = Math.max(0, Math.min(count - 1, currentIndex + delta))
    }

    function chooseSelected() {
        if (currentIndex >= 0 && currentIndex < count)
            tabChosen(model[currentIndex].tab)
    }

    function closeSelected() {
        if (currentIndex >= 0 && currentIndex < count)
            tabCloseRequested(model[currentIndex].tab)
    }

    clip: true
    currentIndex: 0
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar {}

    delegate: Column {
        id: item

        required property int index
        required property var modelData

        width: ListView.view.width

        TabSearchSection {
            visible: list.showsSections && list.isFirstOfWindow(item.index)
            height: visible ? implicitHeight : 0
            width: parent.width
            windowNumber: item.modelData.windowNumber
        }

        TabSearchRow {
            width: parent.width
            entry: item.modelData
            highlighted: ListView.isCurrentItem
            onHoveredChanged: if (hovered) list.currentIndex = item.index
            onClicked: list.tabChosen(item.modelData.tab)
            onCloseRequested: list.tabCloseRequested(item.modelData.tab)
        }
    }
}
