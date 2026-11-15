import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Popup {
    id: root

    required property var tab

    signal manageRequested()
    signal otherSiteFillRequested(var login)

    function closeAndFocusPage() {
        close()
        if (tab)
            tab.focusPage()
    }

    function handleEscape() {
        if (search.text === "") {
            closeAndFocusPage()
            return
        }
        search.clear()
        search.forceActiveFocus()
    }

    function fill(login) {
        tab.passwords.fill(login.origin, login.username)
        close()
    }

    function askToFill(login) {
        close()
        otherSiteFillRequested(login)
    }

    function closeIfUnavailable() {
        if (!tab || !tab.passwords.isAvailable)
            close()
    }

    width: 360
    padding: Kirigami.Units.largeSpacing
    modal: false
    focus: true
    closePolicy: Popup.CloseOnPressOutside
    onAboutToShow: search.clear()
    onOpened: search.forceActiveFocus()
    onTabChanged: close()

    Connections {
        target: root.tab ? root.tab.passwords : null
        function onAvailabilityChanged() { root.closeIfUnavailable() }
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.smallSpacing
        Keys.onEscapePressed: root.handleEscape()

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

        PanelSearchField {
            id: search
            objectName: "passwordSearchField"
            placeholderText: qsTr("Search passwords")
            enabled: !(root.tab && root.tab.passwords.isWalletUnavailable)
            Layout.fillWidth: true
            onStepDownRequested: list.focusCurrent()
            onOpenRequested: list.activateCurrent()
        }

        SavedLoginList {
            id: list
            tab: root.tab
            searchText: search.text
            Layout.fillWidth: true
            onFillRequested: function(login) { root.fill(login) }
            onOtherSiteRequested: function(login) { root.askToFill(login) }
            onTopReached: search.forceActiveFocus()
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
