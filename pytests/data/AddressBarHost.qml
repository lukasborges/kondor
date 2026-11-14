import QtQuick
import QtQuick.Controls
import Kondor

ApplicationWindow {
    id: window
    width: 800
    height: 300
    visible: true

    property var tabModel
    property alias addressBar: bar

    function openUrl(url, background) {}

    function barProperty(name) { return bar[name] }
    function suggestions() { return Array.from(bar.data).find(child => child.networkSuggestions !== undefined) }
    function suggestionsProperty(name) { return suggestions()[name] }
    function suggestionRowCount() { return suggestions().rows.length }
    function suggestionRowText(index) { return suggestions().selectedText(index) }
    function focusBar() { bar.forceActiveFocus(); return bar.activeFocus }

    AddressBar {
        id: bar
        width: 700
        tabs: window.tabModel
        browserWindow: window
    }
}
