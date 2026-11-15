PROBE_QML = """import QtQuick
QtObject {
    property var strip
    property var model

    function bar() { return strip.tabBar }
    function view() { return strip.tabBar.contentItem }
    function itemOf(tab) { return bar().itemAt(model.indexOfTab(tab)) }
    function itemAtIndex(index) { return bar().itemAt(index) }
    function leftOfItem(item) { return item.mapToItem(strip, 0, 0).x }
    function leftOf(index) { return leftOfItem(itemAtIndex(index)) }
    function leftOfTab(tab) { return leftOfItem(itemOf(tab)) }
    function widthOf(index) { return itemAtIndex(index).width }
    function itemX(index) { return itemAtIndex(index).x }
    function dragShiftOf(tab) { return itemOf(tab).dragShift }
    function stripProp(name) { return strip[name] }
    function barProp(name) { return bar()[name] }
    function viewProp(name) { return view()[name] }
    function buttonProp(button, name) { return strip[button][name] }
    function buttonCenter(button) {
        const item = strip[button]
        return item.mapToItem(null, item.width / 2, item.height / 2)
    }
    function buttonCenterX(button) { return buttonCenter(button).x }
    function buttonCenterY(button) { return buttonCenter(button).y }
    function sceneX(x, y) { return strip.mapToItem(null, x, y).x }
    function sceneY(x, y) { return strip.mapToItem(null, x, y).y }
    function isInsideTabBar(index) {
        const item = itemAtIndex(index)
        const left = item.mapToItem(bar(), 0, 0).x
        return left >= -0.5 && left + item.width <= bar().width + 0.5
    }
    function overlapsButton(index, button) {
        const item = itemAtIndex(index)
        const target = strip[button]
        const left = item.mapToItem(strip, 0, 0).x
        const right = Math.min(left + item.width, target.x + target.width)
        return right - Math.max(left, target.x) > 0.5
    }
    function isFullyInView(index) {
        const item = itemAtIndex(index)
        const contentX = view().contentX
        return item.x >= contentX - 0.5 && item.x + item.width <= contentX + view().width + 0.5
    }
    function isStartOfTabInView(index) {
        const item = itemAtIndex(index)
        const left = item.mapToItem(view(), 0, 0).x
        return left >= -0.5 && left + item.width <= view().width + 0.5
    }
    function closeWithMouse(tab) { strip.closeWithMouse(tab) }
    function scrollTo(position) { strip.scrollTo(position) }
    function emptyAt(x, y) { return strip.emptyAt(x, y) }
    function resize(width) { strip.width = width; strip.height = 36 }
}
"""
STUB_WINDOW_QML = """import QtQml
QtObject {
    property var model
    function closeTabFor(tab) { model.closeTabObject(tab) }
}
"""
STRIP_QML = "import QtQuick\nimport Kondor\nTabStrip {}\n"
