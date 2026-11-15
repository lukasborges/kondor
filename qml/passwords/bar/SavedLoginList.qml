import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ColumnLayout {
    id: root

    required property var tab
    property string searchText: ""
    property var logins: []

    readonly property bool isSearching: searchText.trim() !== ""
    readonly property bool isWalletUnavailable: tab ? tab.passwords.isWalletUnavailable : false

    signal fillRequested(var login)
    signal otherSiteRequested(var login)
    signal topReached()

    function reload() {
        logins = tab && !isWalletUnavailable ? tab.passwords.matches(searchText) : []
    }

    function activate(login) {
        if (!login.isThisSite)
            otherSiteRequested(login)
        else
            fillRequested(login)
    }

    function activateCurrent() {
        if (list.currentIndex >= 0 && list.currentIndex < logins.length)
            activate(logins[list.currentIndex])
    }

    function focusCurrent() {
        if (list.currentItem)
            list.currentItem.forceActiveFocus()
    }

    function step(delta) {
        const target = list.currentIndex + delta
        if (target < 0)
            return topReached()
        list.currentIndex = Math.min(target, list.count - 1)
        focusCurrent()
    }

    spacing: 0
    onSearchTextChanged: reload()
    onTabChanged: reload()
    Component.onCompleted: reload()

    Connections {
        target: root.tab ? root.tab.passwords : null
        function onUsernamesChanged() { root.reload() }
        function onWalletStateChanged() { root.reload() }
    }

    Component {
        id: accountRow

        SavedAccountRow {
            required property var modelData
            login: modelData
            width: root.width - scrollBar.width
            tab: root.tab
            onActivated: root.activate(login)
            onStepRequested: function(delta) { root.step(delta) }
        }
    }

    Component {
        id: resultRow

        SavedLoginResultRow {
            required property var modelData
            login: modelData
            width: root.width - scrollBar.width
            tab: root.tab
            onActivated: root.activate(login)
            onStepRequested: function(delta) { root.step(delta) }
        }
    }

    ListView {
        id: list

        visible: count > 0
        Layout.fillWidth: true
        Layout.preferredHeight: Math.min(contentHeight, Kirigami.Units.gridUnit * 18)
        clip: true
        model: root.logins
        delegate: root.isSearching ? resultRow : accountRow
        ScrollBar.vertical: ScrollBar { id: scrollBar }
    }

    Kirigami.PlaceholderMessage {
        visible: list.count === 0
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.largeSpacing
        text: root.isWalletUnavailable ? qsTr("Passwords Unavailable")
              : root.isSearching ? qsTr("No Matches")
              : qsTr("No Passwords for This Site")
        explanation: root.isWalletUnavailable
            ? qsTr("KWallet is disabled or access to it was denied, so passwords cannot be saved or filled.")
            : ""
    }
}
