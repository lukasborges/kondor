import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

StackLayout {
    id: root

    required property SettingsDraft draft
    required property TabModel tabModel
    required property int tab

    Layout.fillWidth: true
    Layout.fillHeight: true
    currentIndex: root.tab

    function commitHomePage(text) {
        const isBlank = text.trim().length === 0
        root.draft.homePage = isBlank ? "" : ProfileManager.resolveAddress(text).toString()
    }

    function useCurrentPage() {
        const tab = root.tabModel.currentTab
        if (tab)
            root.draft.homePage = tab.url.toString()
    }

    ScrollView {
        id: startupView
        contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            width: startupView.availableWidth
            spacing: Kirigami.Units.largeSpacing

            Kirigami.FormLayout {
                Layout.fillWidth: true

                RadioButton {
                    id: homePageRadio
                    Kirigami.FormData.label: qsTr("On startup:")
                    text: qsTr("Open the home page")
                    onClicked: root.draft.startupBehavior = "homepage"
                }

                Binding {
                    target: homePageRadio
                    property: "checked"
                    value: root.draft.startupBehavior === "homepage"
                }

                RadioButton {
                    id: restoreRadio
                    text: qsTr("Open the tabs from last time")
                    onClicked: root.draft.startupBehavior = "restore"
                }

                Binding {
                    target: restoreRadio
                    property: "checked"
                    value: root.draft.startupBehavior === "restore"
                }

                Item { Kirigami.FormData.isSection: true }

                TextField {
                    id: homeField
                    Kirigami.FormData.label: qsTr("Home page:")
                    placeholderText: qsTr("New Tab page")
                    Layout.preferredWidth: Kirigami.Units.gridUnit * 18
                    onTextEdited: root.draft.homePage = text
                    onEditingFinished: root.commitHomePage(text)
                }

                Binding {
                    target: homeField
                    property: "text"
                    value: root.draft.homePage
                }

                RowLayout {
                    Button {
                        text: qsTr("Use Current Page")
                        icon.name: "go-home"
                        enabled: root.tabModel.currentTab !== null
                                 && !root.tabModel.currentTab.isPrivate
                        onClicked: root.useCurrentPage()
                    }

                    Button {
                        text: qsTr("Use New Tab Page")
                        icon.name: "tab-new"
                        enabled: root.draft.homePage.length > 0
                        onClicked: root.draft.homePage = ""
                    }
                }
            }

            Item { Layout.fillHeight: true }
        }
    }

    ScrollView {
        id: newTabsView
        contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            width: newTabsView.availableWidth
            spacing: Kirigami.Units.largeSpacing

            Kirigami.FormLayout {
                Layout.fillWidth: true

                CheckBox {
                    id: topSitesCheck
                    Kirigami.FormData.label: qsTr("New Tab page:")
                    text: qsTr("Show top sites")
                    onToggled: root.draft.showTopSites = checked
                }

                Binding {
                    target: topSitesCheck
                    property: "checked"
                    value: root.draft.showTopSites
                }

                Button {
                    text: qsTr("Restore Removed Sites")
                    icon.name: "edit-undo"
                    enabled: Settings.hiddenTopSites.length > 0
                    onClicked: Settings.hiddenTopSites = []
                }
            }

            Item { Layout.fillHeight: true }
        }
    }
}
