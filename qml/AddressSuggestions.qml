import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// Dropdown under the address bar. Its rows are, in this order: visiting the
// typed address and searching for it (#44), matching bookmarks, matching
// history entries and the search engine's suggestions (#11). Focus stays in
// the field: the bar owns the keyboard and inline completion.
Popup {
    id: root

    padding: 0
    focus: false
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    // Typed text the rows are built from; programmatic changes to the address
    // bar (selected rows, inline completion) must not rebuild them.
    property string text
    property int currentIndex: 0
    // Search-engine suggestions that arrived for `text`; cleared on every edit.
    property var networkSuggestions: []

    readonly property int maxRows: 10

    readonly property var rows: buildRows()

    signal navigate(url url, bool background)

    onTextChanged: networkSuggestions = []

    function buildRows() {
        const typed = text.trim()
        if (typed.length === 0)
            return []

        const rows = []
        const seen = ({})

        // #44 rows: for an address, visiting it (selected) and searching for
        // the same text; otherwise only the search row.
        const address = String(ProfileManager.addressUrl(typed))
        if (address.length > 0) {
            rows.push({
                iconName: "globe",
                label: address,
                suffix: qsTr("Visit"),
                url: address,
                fieldText: address
            })
            seen[address] = true
        }

        const engineName = Settings.searchEngineName()
        //: %1 is the search engine name
        const searchSuffix = engineName.length > 0
            ? qsTr("Search with %1").arg(engineName)
            : qsTr("Search")
        rows.push({
            iconName: "edit-find",
            label: typed,
            suffix: searchSuffix,
            url: ProfileManager.searchUrl(typed),
            fieldText: typed
        })

        // Bookmarks (#2) and history (#1) only ever read persistent data, so
        // they are safe to show while a private tab is focused.
        const bookmarks = BookmarkManager.search(typed, 4)
        for (let i = 0; i < bookmarks.length; ++i) {
            const bookmark = bookmarks[i]
            const url = String(bookmark.url)
            if (url.length === 0 || seen[url])
                continue
            seen[url] = true
            rows.push({
                iconName: "bookmarks",
                label: String(bookmark.title).length > 0 ? String(bookmark.title) : url,
                suffix: url,
                url: url,
                fieldText: url
            })
        }

        const history = HistoryManager.suggest(typed, 6)
        for (let i = 0; i < history.length; ++i) {
            const entry = history[i]
            const url = String(entry.url)
            if (url.length === 0 || seen[url])
                continue
            seen[url] = true
            rows.push({
                iconName: "view-history",
                label: String(entry.title).length > 0 ? String(entry.title) : url,
                suffix: url,
                url: url,
                fieldText: url
            })
        }

        // Network suggestions carry no URL of their own: activating one
        // searches for it.
        for (let i = 0; i < networkSuggestions.length; ++i) {
            const suggestion = String(networkSuggestions[i])
            if (suggestion.length === 0)
                continue
            rows.push({
                iconName: "edit-find",
                label: suggestion,
                suffix: "",
                url: ProfileManager.searchUrl(suggestion),
                fieldText: suggestion
            })
        }

        return rows.slice(0, maxRows)
    }

    function activate(index, background) {
        if (index < 0 || index >= rows.length)
            return
        navigate(rows[index].url, background === true)
    }

    // Text the address bar shows when the row is selected with the keyboard:
    // the typed/suggested search text rather than the engine's search URL.
    function selectedText(index) {
        if (index < 0 || index >= rows.length)
            return ""
        return String(rows[index].fieldText)
    }

    onRowsChanged: {
        if (currentIndex >= rows.length)
            currentIndex = Math.max(0, rows.length - 1)
    }

    contentItem: ColumnLayout {
        spacing: 0

        Repeater {
            model: root.rows

            delegate: ItemDelegate {
                id: row
                required property var modelData
                required property int index

                Layout.fillWidth: true
                focusPolicy: Qt.NoFocus
                highlighted: row.index === root.currentIndex
                onClicked: root.activate(row.index, false)

                contentItem: RowLayout {
                    spacing: Kirigami.Units.largeSpacing

                    Kirigami.Icon {
                        source: row.modelData.iconName
                        Layout.preferredWidth: 16
                        Layout.preferredHeight: 16
                    }

                    Label {
                        text: row.modelData.label
                        elide: Text.ElideRight
                        Layout.maximumWidth: 420
                    }

                    Label {
                        visible: row.modelData.suffix.length > 0
                        text: "— " + row.modelData.suffix
                        color: row.highlighted ? Kirigami.Theme.highlightedTextColor
                                               : Kirigami.Theme.disabledTextColor
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }

                    Item {
                        visible: row.modelData.suffix.length === 0
                        Layout.fillWidth: true
                    }
                }

                // Middle click opens the row in a background tab.
                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.MiddleButton
                    onClicked: root.activate(row.index, true)
                }
            }
        }
    }
}
