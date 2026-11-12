import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Popup {
    id: root

    padding: 0
    focus: false
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    property string text
    property int currentIndex: 0
    property var networkSuggestions: []

    readonly property int maxRows: 10

    readonly property var rows: buildRows()

    signal navigate(url url, bool background)

    onTextChanged: networkSuggestions = []

    function buildRows() {
        const typed = root.text.trim()
        return typed.length === 0 ? [] : root.buildRowsFor(typed)
    }

    function buildRowsFor(typed) {
        const rows = []
        const seen = ({})
        root.appendUnique(rows, seen, root.visitRow(typed))
        rows.push(root.searchRow(typed))
        root.appendMatches(rows, seen, typed)
        return rows.concat(root.networkRows()).slice(0, root.maxRows)
    }

    function appendMatches(rows, seen, typed) {
        BookmarkManager.search(typed, 4).forEach(function(bookmark) {
            root.appendUnique(rows, seen, root.matchRow("bookmarks", bookmark))
        })
        HistoryManager.suggest(typed, 6).forEach(function(entry) {
            root.appendUnique(rows, seen, root.matchRow("view-history", entry))
        })
    }

    function appendUnique(rows, seen, row) {
        if (row.url.length === 0 || seen[row.url])
            return
        seen[row.url] = true
        rows.push(row)
    }

    function visitRow(typed) {
        const address = String(ProfileManager.addressUrl(typed))
        return { iconName: "globe", label: address, suffix: qsTr("Visit"),
                 url: address, fieldText: address }
    }

    function searchRow(typed) {
        const engineName = Settings.searchEngineName()
        //: %1 is the search engine name
        const suffix = engineName.length > 0 ? qsTr("Search with %1").arg(engineName) : qsTr("Search")
        return { iconName: "edit-find", label: typed, suffix: suffix,
                 url: ProfileManager.searchUrl(typed), fieldText: typed }
    }

    function matchRow(iconName, entry) {
        const url = String(entry.url)
        const title = String(entry.title)
        return { iconName: iconName, label: title.length > 0 ? title : url,
                 suffix: url, url: url, fieldText: url }
    }

    function networkRows() {
        return root.networkSuggestions.map(String).filter(function(suggestion) {
            return suggestion.length > 0
        }).map(function(suggestion) {
            return { iconName: "edit-find", label: suggestion, suffix: "",
                     url: ProfileManager.searchUrl(suggestion), fieldText: suggestion }
        })
    }

    function activate(index, background) {
        if (index < 0 || index >= rows.length)
            return
        navigate(rows[index].url, background === true)
    }

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

                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.MiddleButton
                    onClicked: root.activate(row.index, true)
                }
            }
        }
    }
}
