import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Popup {
    id: root

    required property var tab

    signal manageRequested()

    function focusRow(index) {
        const row = rows.itemAt(Math.max(0, Math.min(index, rows.count - 1)))
        if (row)
            row.forceActiveFocus()
    }

    function closeIfNoAccounts() {
        if (!tab || tab.passwords.usernames.length === 0)
            close()
    }

    width: 360
    padding: Kirigami.Units.largeSpacing
    modal: false
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    onOpened: focusRow(0)
    onTabChanged: close()

    Connections {
        target: root.tab ? root.tab.passwords : null
        function onUsernamesChanged() { root.closeIfNoAccounts() }
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.smallSpacing

        RowLayout {
            spacing: Kirigami.Units.largeSpacing

            Kirigami.Icon {
                source: "dialog-password"
                Layout.preferredWidth: 32
                Layout.preferredHeight: 32
            }

            ColumnLayout {
                spacing: 0

                Kirigami.Heading {
                    level: 4
                    text: qsTr("Saved Passwords")
                }

                Label {
                    text: root.tab ? root.tab.passwords.host : ""
                    color: Kirigami.Theme.disabledTextColor
                }
            }
        }

        Repeater {
            id: rows
            model: root.tab ? root.tab.passwords.usernames : []

            SavedAccountRow {
                required property int index
                required property string modelData
                username: modelData
                tab: root.tab
                onFillRequested: root.close()
                onStepRequested: function(step) { root.focusRow(index + step) }
            }
        }

        Kirigami.Separator { Layout.fillWidth: true }

        Button {
            text: qsTr("Manage Passwords…")
            icon.name: "configure"
            flat: true
            onClicked: {
                root.close()
                root.manageRequested()
            }
        }
    }
}
