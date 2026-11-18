import QtQuick
import org.kde.kirigami as Kirigami

QtObject {
    id: layout

    required property var tabStrip

    readonly property int revision: tabStrip.tabModel.groupRevision
    readonly property real namedLabelWidth: Kirigami.Units.gridUnit * 6
    readonly property real unnamedLabelWidth: Kirigami.Units.gridUnit * 2
    readonly property real countWidth: Kirigami.Units.gridUnit * 1.5
    readonly property real labelsWidth: revision >= 0 ? sumLabelWidths() : 0

    function labelWidthOf(group) {
        const base = group.name.length > 0 ? namedLabelWidth : unnamedLabelWidth
        return group.collapsed ? base + countWidth : base
    }

    function sumLabelWidths() {
        return tabStrip.tabModel.groups.reduce((sum, group) => sum + labelWidthOf(group), 0)
    }

    function leadWidth(index) {
        const model = tabStrip.tabModel
        return revision >= 0 && model.isGroupStart(index) ? labelWidthOf(model.groupAt(index)) : 0
    }

    function bodyWidth(index) {
        if (index < tabStrip.pinnedCount)
            return tabStrip.pinnedTabWidth
        return revision >= 0 && tabStrip.tabModel.isHiddenByGroup(index) ? 0 : tabStrip.tabWidth
    }

    function slotWidth(index) {
        return leadWidth(index) + bodyWidth(index)
    }

    function slotX(index) {
        let x = 0
        for (let i = 0; i < index; ++i)
            x += slotWidth(i)
        return x
    }

    function indexAtX(x) {
        const last = tabStrip.tabModel.count - 1
        let left = 0
        for (let i = 0; i < last; ++i) {
            left += slotWidth(i)
            if (x < left)
                return i
        }
        return Math.max(0, last)
    }

    function moveGroupTo(group, sceneX) {
        const model = tabStrip.tabModel
        const x = tabStrip.tabBar.contentItem.mapFromItem(null, sceneX, 0).x - tabStrip.scroller.origin
        const row = indexAtX(x)
        const first = model.firstIndexOf(group)
        model.moveGroup(group, row >= first ? row - model.tabCountOf(group) + 1 : row)
    }
}
