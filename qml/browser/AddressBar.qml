import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kondor

TextField {
    id: root

    required property TabModel tabs
    required property var browserWindow

    readonly property alias bookmarkEditor: buttons.bookmarkEditor

    function syncFromTab() {
        if (activeFocus)
            return
        const tab = tabs.currentTab
        text = (tab && !tab.newTabPage) ? tab.url.toString() : ""
    }

    function focusAndSelectAll() {
        forceActiveFocus()
        selectAll()
    }

    function openSuggestion(url, background) {
        if (background)
            browserWindow.openUrl(url, true)
        else if (tabs.currentTab)
            tabs.currentTab.navigateTo(url)
        suggestionsPopup.close()
        focus = false
    }

    Layout.fillWidth: true
    Layout.leftMargin: 8
    Layout.rightMargin: 8
    placeholderText: qsTr("Search or enter address")
    selectByMouse: true
    leftPadding: security.visible ? security.width + 8 : 8
    rightPadding: buttons.width > 0 ? buttons.width + 10 : 8

    onAccepted: completer.acceptText()
    onTextEdited: completer.registerEdit()
    Keys.onDownPressed: function(event) { completer.moveDown(event) }
    Keys.onUpPressed: function(event) { completer.moveUp(event) }
    Keys.onEscapePressed: function(event) { completer.restoreTypedText(event) }
    Component.onCompleted: syncFromTab()

    onActiveFocusChanged: {
        if (activeFocus)
            completer.startTyping()
        else
            completer.stopTyping()
    }

    AddressCompleter {
        id: completer
        field: root
        suggestions: suggestionsPopup
        timer: suggestionsTimer
        tabs: root.tabs
    }

    Timer {
        id: suggestionsTimer
        interval: 120
        onTriggered: completer.updateSuggestions()
    }

    SiteSecurityButton {
        id: security
        anchors.left: parent.left
        anchors.leftMargin: 2
        anchors.verticalCenter: parent.verticalCenter
        tabs: root.tabs
        addressField: root
    }

    AddressBarButtons {
        id: buttons
        anchors.right: parent.right
        anchors.rightMargin: 3
        anchors.verticalCenter: parent.verticalCenter
        tabs: root.tabs
        addressField: root
    }

    AddressSuggestions {
        id: suggestionsPopup
        x: 0
        y: root.height
        width: root.width
        onNavigate: function(url, background) { root.openSuggestion(url, background) }
    }

    Connections {
        target: SearchSuggestions
        function onSuggestionsReady(text, items) {
            if (text === suggestionsPopup.text)
                suggestionsPopup.networkSuggestions = items
        }
    }

    Connections {
        target: root.tabs
        function onCurrentTabChanged() {
            completer.stopTyping()
            root.syncFromTab()
        }
    }

    Connections {
        target: root.tabs.currentTab
        function onUrlChanged() { root.syncFromTab() }
        function onNewTabPageChanged() { root.syncFromTab() }
    }
}
