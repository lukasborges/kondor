import QtQuick
import org.kde.kirigami as Kirigami

QtObject {
    id: layout

    required property var tabStrip

    readonly property var model: tabStrip.stripModel
    readonly property int revision: model.revision
    readonly property real namedLabelWidth: Kirigami.Units.gridUnit * 6
    readonly property real unnamedLabelWidth: Kirigami.Units.gridUnit * 2
    readonly property real countWidth: Kirigami.Units.gridUnit * 1.5
    readonly property real labelsWidth: revision >= 0 ? sumLabelWidths() : 0

    readonly property real labelPadding: Kirigami.Units.smallSpacing * 4

    property TextMetrics nameMetrics: TextMetrics {
        font.bold: true
    }

    function nameWidthOf(group) {
        nameMetrics.text = group.name
        return Math.min(namedLabelWidth, Math.ceil(nameMetrics.advanceWidth) + labelPadding)
    }

    function labelWidthOf(group) {
        const base = group.name.length > 0 ? nameWidthOf(group) : unnamedLabelWidth
        return group.collapsed ? base + countWidth : base
    }

    function sumLabelWidths() {
        return tabStrip.tabModel.groups.reduce((sum, group) => sum + labelWidthOf(group), 0)
    }

    function rowWidth(row) {
        if (revision < 0)
            return 0
        return model.isLabel(row) ? labelWidthOf(model.groupAt(row)) : bodyWidth(row)
    }

    function bodyWidth(row) {
        if (model.tabIndexAt(row) < tabStrip.pinnedCount)
            return tabStrip.pinnedTabWidth
        return model.isHidden(row) ? 0 : tabStrip.tabWidth
    }

    function slotX(row) {
        let x = 0
        for (let i = 0; i < row; ++i)
            x += rowWidth(i)
        return x
    }

    function rowAtX(x) {
        const last = model.count - 1
        let left = 0
        for (let i = 0; i < last; ++i) {
            left += rowWidth(i)
            if (x < left)
                return i
        }
        return Math.max(0, last)
    }

    function otherTabsBefore(group, left) {
        let count = 0
        for (let row = 0; row < model.count; ++row)
            count += isOtherTabBefore(row, group, left) ? 1 : 0
        return count
    }

    function isOtherTabBefore(row, group, left) {
        if (model.isLabel(row) || model.groupAt(row) === group)
            return false
        return slotX(row) + rowWidth(row) / 2 < left
    }

    function moveGroupBy(group, shift) {
        const left = slotX(model.rowOfLabel(group)) + shift
        tabStrip.tabModel.moveGroup(group, otherTabsBefore(group, left))
    }
}
