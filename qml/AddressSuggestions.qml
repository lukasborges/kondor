import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// Dropdown under the address bar. When the typed text looks like an address it
// offers visiting it (selected) and searching for the same text with the
// configured engine. Focus stays in the field; #11 extends the row list with
// history, bookmarks and network suggestions.
Popup {
    id: root

    padding: 0
    focus: false
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    property string text
    property int currentIndex: 0

    // Rebuilt when the text changes: empty unless it looks like an address.
    readonly property var rows: buildRows()

    signal navigate(url url)

    function buildRows() {
        // QML url values are strings: an empty QUrl converts to "".
        const address = String(ProfileManager.addressUrl(text))
        if (address.length === 0)
            return []

        const engineName = Settings.searchEngineName()
        //: %1 is the search engine name
        const searchSuffix = engineName.length > 0
            ? qsTr("Search with %1").arg(engineName)
            : qsTr("Search")

        return [
            {
                iconName: "globe",
                label: address,
                suffix: qsTr("Visit"),
                url: address
            },
            {
                iconName: "edit-find",
                label: text.trim(),
                suffix: searchSuffix,
                url: ProfileManager.searchUrl(text)
            }
        ]
    }

    function activate(index) {
        if (index < 0 || index >= rows.length)
            return
        navigate(rows[index].url)
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
                onClicked: root.activate(row.index)

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
                        text: "— " + row.modelData.suffix
                        color: row.highlighted ? Kirigami.Theme.highlightedTextColor
                                               : Kirigami.Theme.disabledTextColor
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                }
            }
        }
    }
}
