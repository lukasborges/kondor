import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ScrollView {
    id: root

    required property SettingsDraft draft

    contentWidth: availableWidth
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

    ColumnLayout {
        width: root.availableWidth
        spacing: Kirigami.Units.largeSpacing

        Kirigami.FormLayout {
            Layout.fillWidth: true

            ComboBox {
                id: engineBox
                Kirigami.FormData.label: qsTr("Search engine:")
                Layout.preferredWidth: Kirigami.Units.gridUnit * 14
                model: [
                    { value: "duckduckgo", label: "DuckDuckGo" },
                    { value: "google", label: "Google" },
                    { value: "startpage", label: "Startpage" },
                    { value: "brave", label: "Brave Search" },
                    { value: "custom", label: qsTr("Custom…") }
                ]
                textRole: "label"
                valueRole: "value"
                onActivated: root.draft.searchEngine = currentValue
            }

            Binding {
                target: engineBox
                property: "currentIndex"
                value: Math.max(0, engineBox.indexOfValue(root.draft.searchEngine))
            }

            TextField {
                id: customField
                Kirigami.FormData.label: qsTr("Custom URL:")
                Layout.preferredWidth: Kirigami.Units.gridUnit * 18
                enabled: root.draft.searchEngine === "custom"
                placeholderText: "https://www.bing.com/search?q=%1"
                onTextEdited: root.draft.customSearchUrl = text
                onEditingFinished: root.draft.customSearchUrl = text
            }

            Binding {
                target: customField
                property: "text"
                value: root.draft.customSearchUrl
            }

            CheckBox {
                id: suggestionsCheck
                text: qsTr("Show search suggestions in the address bar")
                onToggled: root.draft.searchSuggestions = checked
            }

            Binding {
                target: suggestionsCheck
                property: "checked"
                value: root.draft.searchSuggestions
            }
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: root.draft.searchEngine === "custom"
                     && root.draft.customSearchUrl.indexOf("%1") === -1
            type: Kirigami.MessageType.Warning
            text: qsTr("The URL must contain “%1” where the search terms go.").arg("%1")
        }

        Item { Layout.fillHeight: true }
    }
}
