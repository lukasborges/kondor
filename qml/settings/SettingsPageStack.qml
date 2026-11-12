pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

StackLayout {
    id: root

    required property SettingsDraft draft
    required property SettingsPages catalog
    required property TabModel tabModel
    required property int generalTab
    required property int passwordsTab

    readonly property var pageComponents: [generalPage, searchPage, downloadsPage,
        privacyPage, passwordsPage, extensionsPage, spellingPage]

    objectName: "pageStack"
    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.margins: Kirigami.Units.gridUnit

    Repeater {
        model: root.catalog.pages

        delegate: Loader {
            required property int index
            Layout.fillWidth: true
            Layout.fillHeight: true
            sourceComponent: root.pageComponents[index]
        }
    }

    Component {
        id: generalPage
        GeneralSettingsPage {
            draft: root.draft
            tabModel: root.tabModel
            tab: root.generalTab
        }
    }

    Component {
        id: searchPage
        SearchSettingsPage { draft: root.draft }
    }

    Component {
        id: downloadsPage
        DownloadsSettingsPage { draft: root.draft }
    }

    Component {
        id: privacyPage
        PrivacySettingsPage { draft: root.draft }
    }

    Component {
        id: passwordsPage
        PasswordsPage {
            Layout.fillWidth: true
            Layout.fillHeight: true
            tab: root.passwordsTab
            offerToSave: root.draft.offerToSavePasswords
            onOfferToSaveToggled: function(checked) { root.draft.offerToSavePasswords = checked }
        }
    }

    Component {
        id: extensionsPage
        ExtensionsPage {
            Layout.fillWidth: true
            Layout.fillHeight: true
            autoUpdate: root.draft.extensionsAutoUpdate
            onAutoUpdateToggled: function(checked) { root.draft.extensionsAutoUpdate = checked }
        }
    }

    Component {
        id: spellingPage
        SpellingSettingsPage { draft: root.draft }
    }
}
