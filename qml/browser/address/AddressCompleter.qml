import QtQuick
import QtQuick.Controls
import Kondor

QtObject {
    id: root

    required property TextField field
    required property AddressSuggestions suggestions
    required property Timer timer
    required property TabModel tabs

    property string typedText: ""
    property string previousText: ""
    property int previousTypedLength: 0
    property bool lastEditDeleted: false

    function rememberText(text) {
        previousText = text
        previousTypedLength = text.length
    }

    function startTyping() {
        typedText = field.text
        rememberText(field.text)
        lastEditDeleted = false
        field.selectAll()
    }

    function stopTyping() {
        suggestions.close()
        SearchSuggestions.cancel()
    }

    function registerEdit() {
        lastEditDeleted = field.text.length < previousText.length
                && field.text.length <= previousTypedLength
        rememberText(field.text)
        typedText = field.text
        timer.restart()
    }

    function completeHost() {
        const typed = field.text
        if (lastEditDeleted || typed.length < 2)
            return
        const host = HistoryManager.hostCompletion(typed)
        if (host.length === 0)
            return
        field.text = host
        previousText = host
        previousTypedLength = typed.length
        field.select(typed.length, host.length)
    }

    function updateSuggestions() {
        if (!field.activeFocus || field.text.trim().length === 0) {
            stopTyping()
            return
        }
        completeHost()
        const query = field.text.trim()
        showRows(query)
        requestNetworkSuggestions(query)
    }

    function showRows(query) {
        suggestions.text = query
        suggestions.currentIndex = 0
        suggestions.open()
    }

    function requestNetworkSuggestions(query) {
        const tab = tabs.currentTab
        if (Settings.searchSuggestions && tab && !tab.isPrivate) {
            SearchSuggestions.request(query)
            return
        }
        SearchSuggestions.cancel()
        suggestions.networkSuggestions = []
    }

    function flushPendingQuery() {
        if (!timer.running)
            return
        timer.stop()
        updateSuggestions()
    }

    function moveDown(event) {
        moveSelection(event, 1)
    }

    function moveUp(event) {
        moveSelection(event, -1)
    }

    function moveSelection(event, delta) {
        flushPendingQuery()
        event.accepted = suggestions.opened
        if (suggestions.opened)
            selectRow(nextIndex(delta))
    }

    function nextIndex(delta) {
        const wanted = suggestions.currentIndex + delta
        return delta > 0 ? Math.min(wanted, suggestions.rows.length - 1) : Math.max(wanted, 0)
    }

    function selectRow(index) {
        suggestions.currentIndex = index
        field.text = suggestions.selectedText(index)
        rememberText(field.text)
    }

    function restoreTypedText(event) {
        timer.stop()
        event.accepted = suggestions.opened
        if (!suggestions.opened)
            return
        field.text = typedText
        rememberText(typedText)
        suggestions.close()
    }

    function acceptText() {
        const tab = tabs.currentTab
        if (!tab)
            return
        if (suggestions.opened && !timer.running)
            suggestions.activate(suggestions.currentIndex, false)
        else
            navigateToTypedText(tab)
    }

    function navigateToTypedText(tab) {
        timer.stop()
        suggestions.close()
        tab.navigateTo(ProfileManager.resolveAddress(field.text))
        field.focus = false
    }
}
