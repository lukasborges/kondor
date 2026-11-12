import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// Ad and tracker blocking for the current site, opened from the shield button
// in the address bar: blocked count, per-site switch and a list refresh.
Popup {
    id: root

    property Tab tab: null
    property string host: ""
    property int blockedCount: 0
    property bool siteAllowed: false

    width: 340
    padding: Kirigami.Units.largeSpacing
    modal: false
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    function refresh() {
        blockedCount = AdBlockManager.blockedCount(host)
        siteAllowed = AdBlockManager.isAllowed(host)
    }

    function lastUpdateText() {
        const date = AdBlockManager.lastUpdate
        if (AdBlockManager.updating)
            return qsTr("Updating lists…")
        if (isNaN(date.getTime()))
            return qsTr("Lists not downloaded yet")
        return qsTr("Lists updated %1").arg(date.toLocaleString(Qt.locale(), Locale.ShortFormat))
    }

    onHostChanged: refresh()
    onAboutToShow: refresh()

    Connections {
        target: AdBlockManager
        function onBlockedCountChanged(changedHost) {
            if (changedHost === root.host)
                root.blockedCount = AdBlockManager.blockedCount(root.host)
        }
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        RowLayout {
            spacing: Kirigami.Units.largeSpacing

            Kirigami.Icon {
                source: root.siteAllowed || !AdBlockManager.enabled ? "security-low" : "security-high"
                Layout.preferredWidth: 32
                Layout.preferredHeight: 32
            }

            ColumnLayout {
                spacing: 0
                Layout.fillWidth: true

                Kirigami.Heading {
                    level: 4
                    text: qsTr("Blocked on this page: %1").arg(root.blockedCount)
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                }

                Label {
                    text: root.host
                    color: Kirigami.Theme.disabledTextColor
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                }
            }
        }

        Kirigami.Separator { Layout.fillWidth: true }

        Switch {
            id: siteSwitch
            text: qsTr("Blocking enabled on this site")
            enabled: AdBlockManager.enabled
            checked: !root.siteAllowed && AdBlockManager.enabled
            onToggled: {
                // A private tab never writes its choice to disk.
                AdBlockManager.setAllowed(root.host, !checked,
                                          root.tab ? !root.tab.isPrivate : true)
                root.siteAllowed = AdBlockManager.isAllowed(root.host)
                if (root.tab)
                    root.tab.reload()
            }
        }

        Label {
            visible: !AdBlockManager.enabled
            text: qsTr("Ad and tracker blocking is turned off in Settings.")
            wrapMode: Text.WordWrap
            color: Kirigami.Theme.disabledTextColor
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.fillWidth: true

            Label {
                text: root.lastUpdateText()
                font: Kirigami.Theme.smallFont
                color: Kirigami.Theme.disabledTextColor
                Layout.fillWidth: true
                elide: Text.ElideRight
            }

            Button {
                text: qsTr("Update Lists Now")
                icon.name: "view-refresh"
                flat: true
                enabled: !AdBlockManager.updating
                onClicked: AdBlockManager.updateLists()
            }
        }
    }
}
