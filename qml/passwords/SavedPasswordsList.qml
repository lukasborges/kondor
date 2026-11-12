import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import Kondor

PasswordsFrame {
    id: root

    required property bool walletDenied
    required property string filter
    required property RevealedPasswords revealed
    signal addRequested
    signal deleteRequested(string origin, string username)

    readonly property string needle: root.filter.trim()
    readonly property bool isFiltering: root.needle !== ""

    function matchesNeedle(entry) {
        const needle = root.needle.toLowerCase()
        return needle === "" || entry.host.toLowerCase().includes(needle)
            || entry.username.toLowerCase().includes(needle)
    }

    function compareEntries(a, b) {
        return a.host.localeCompare(b.host) || a.origin.localeCompare(b.origin)
            || a.username.localeCompare(b.username)
    }

    function rebuild() {
        const list = PasswordStore.entries.filter(root.matchesNeedle).sort(root.compareEntries)
        savedModel.clear()
        for (const entry of list)
            savedModel.append({ site: entry.host, origin: entry.origin, username: entry.username })
        savedList.currentIndex = -1
    }

    function indexOfLogin(origin, username) {
        for (let i = 0; i < savedModel.count; ++i) {
            const row = savedModel.get(i)
            if (row.origin === origin && row.username === username)
                return i
        }
        return -1
    }

    function select(origin, username) {
        const index = root.indexOfLogin(origin, username)
        if (index < 0)
            return
        savedList.currentIndex = index
        savedList.positionViewAtIndex(index, ListView.Contain)
    }

    function onStoreChanged() {
        root.rebuild()
        root.revealed.clear()
    }

    enabled: !root.walletDenied
    onFilterChanged: root.rebuild()

    Connections {
        target: PasswordStore
        function onChanged() { root.onStoreChanged() }
    }

    ListModel { id: savedModel }

    Kirigami.PlaceholderMessage {
        anchors.centerIn: parent
        width: parent.width - Kirigami.Units.gridUnit * 4
        visible: !root.walletDenied && savedModel.count === 0
        icon.name: root.isFiltering ? "edit-none" : "dialog-password"
        text: root.isFiltering ? qsTr("No saved passwords match “%1”").arg(root.needle)
                               : qsTr("No saved passwords")
        explanation: root.isFiltering ? "" : qsTr("Kondor offers to save a password when you log in to a site. You can also add one here, or import the CSV file exported by another browser or password manager.")
        helpfulAction: root.isFiltering ? null : addAction

        Kirigami.Action {
            id: addAction
            text: qsTr("Add Password…")
            icon.name: "list-add"
            onTriggered: root.addRequested()
        }
    }

    ListView {
        id: savedList
        anchors.fill: parent
        clip: true
        visible: !root.walletDenied
        highlightFollowsCurrentItem: false
        model: savedModel
        section.property: "site"
        section.delegate: Kirigami.ListSectionHeader {
            required property string section
            width: ListView.view.width
            text: section
        }

        delegate: SavedPasswordDelegate {
            revealed: root.revealed
            onDeleteRequested: function(origin, username) { root.deleteRequested(origin, username) }
        }
    }
}
