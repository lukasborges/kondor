import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// Find bar (Ctrl+F): incremental search, match counter, match case.
InlineBar {
    id: root

    property Tab tab: null
    property Tab previousTab: null

    visible: false

    // Esc closes the bar without stealing the key from the web page: only
    // events already routed inside the bar (field, buttons) reach this handler.
    Keys.onEscapePressed: function(event) {
        event.accepted = true
        root.close()
    }

    function open() {
        visible = true
        searchField.forceActiveFocus()
        searchField.selectAll()
        runSearch()
    }

    function close() {
        if (tab) {
            tab.stopFind()
            tab.setFindResult(0, 0)
        }
        visible = false
    }

    function findNext() {
        runSearch(false)
    }

    function findPrevious() {
        runSearch(true)
    }

    function runSearch(backward) {
        if (!tab)
            return
        if (searchField.text.length === 0) {
            // Clearing the field must also drop the highlights left on the page.
            tab.stopFind()
            tab.setFindResult(0, 0)
            return
        }
        tab.find(searchField.text, backward === true, matchCase.checked)
    }

    onTabChanged: {
        if (previousTab && previousTab !== tab)
            previousTab.stopFind()
        previousTab = tab
        if (visible)
            runSearch()
    }

    // A new page in the same tab starts a fresh search: clear the counter while
    // it loads and look again once the content is ready. Same-document
    // navigations (for example a table-of-contents anchor) do not load, so the
    // previous results stay valid there.
    Connections {
        target: root.tab

        function onLoadingChanged() {
            if (!root.visible)
                return
            if (root.tab.loading)
                root.tab.setFindResult(0, 0)
            else
                root.runSearch()
        }
    }

    Kirigami.Icon {
        source: "edit-find"
        Layout.preferredWidth: 16
        Layout.preferredHeight: 16
    }

    TextField {
        id: searchField
        Layout.preferredWidth: 280
        placeholderText: qsTr("Find in page")
        selectByMouse: true
        onTextChanged: root.runSearch()

        Keys.onPressed: function(event) {
            if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                event.accepted = true
                if (event.modifiers & Qt.ShiftModifier)
                    root.findPrevious()
                else
                    root.findNext()
            }
        }
    }

    ToolButton {
        display: AbstractButton.IconOnly
        icon.name: "go-up"
        enabled: searchField.text.length > 0
        ToolTip.visible: hovered
        ToolTip.text: qsTr("Previous (Shift+F3)")
        ToolTip.delay: 600
        onClicked: root.findPrevious()
    }

    ToolButton {
        display: AbstractButton.IconOnly
        icon.name: "go-down"
        enabled: searchField.text.length > 0
        ToolTip.visible: hovered
        ToolTip.text: qsTr("Next (F3)")
        ToolTip.delay: 600
        onClicked: root.findNext()
    }

    Label {
        Layout.leftMargin: Kirigami.Units.smallSpacing
        visible: searchField.text.length > 0
        text: {
            if (!root.tab)
                return ""
            if (root.tab.findMatches === 0)
                return qsTr("No results")
            return qsTr("%1 of %2").arg(root.tab.findActiveMatch).arg(root.tab.findMatches)
        }
        color: (root.tab && root.tab.findMatches === 0)
               ? Kirigami.Theme.negativeTextColor
               : Kirigami.Theme.disabledTextColor
    }

    CheckBox {
        id: matchCase
        text: qsTr("Match case")
        Layout.leftMargin: Kirigami.Units.largeSpacing
        onToggled: root.runSearch()
    }

    Item {
        Layout.fillWidth: true
    }

    ToolButton {
        display: AbstractButton.IconOnly
        icon.name: "window-close"
        ToolTip.visible: hovered
        ToolTip.text: qsTr("Close (Esc)")
        ToolTip.delay: 600
        onClicked: root.close()
    }
}
