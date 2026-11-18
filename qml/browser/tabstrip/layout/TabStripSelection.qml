import QtQuick

Item {
    id: selection

    required property var tabStrip

    readonly property var model: tabStrip.stripModel
    property bool isChangingRows: false

    function currentRow() {
        const revision = tabStrip.layout.revision
        return revision >= 0 ? model.rowOfTabIndex(tabStrip.tabModel.currentIndex) : -1
    }

    function showCurrentTabInBar() {
        if (tabStrip.tabBar.currentIndex !== currentRow())
            tabStrip.tabBar.currentIndex = currentRow()
    }

    function finishChangingRows() {
        isChangingRows = false
        showCurrentTabInBar()
    }

    function selectRow(row) {
        if (isChangingRows || row < 0 || row === currentRow())
            return
        const index = model.tabIndexAt(row)
        tabStrip.tabModel.setCurrentIndex(model.isLabel(row) ? stepOutOfLabel(row, index) : index)
        showCurrentTabInBar()
    }

    function stepOutOfLabel(row, firstIndex) {
        return currentRow() > row ? Math.max(0, firstIndex - 1) : firstIndex
    }

    Connections {
        target: selection.model
        function onRowsAboutToBeRemoved() { selection.isChangingRows = true }
        function onRowsAboutToBeInserted() { selection.isChangingRows = true }
        function onRowsAboutToBeMoved() { selection.isChangingRows = true }
        function onRowsRemoved() { Qt.callLater(selection.finishChangingRows) }
        function onRowsInserted() { Qt.callLater(selection.finishChangingRows) }
        function onRowsMoved() { Qt.callLater(selection.finishChangingRows) }
    }
}
