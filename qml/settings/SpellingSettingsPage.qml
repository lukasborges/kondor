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

    function setLanguageEnabled(code, isEnabled) {
        const others = root.draft.spellCheckLanguages.filter(other => other !== code)
        root.draft.spellCheckLanguages = isEnabled ? others.concat([code]) : others
    }

    ColumnLayout {
        width: root.availableWidth
        spacing: Kirigami.Units.largeSpacing

        Kirigami.FormLayout {
            Layout.fillWidth: true

            CheckBox {
                id: spellingCheck
                text: qsTr("Check spelling while typing")
                onToggled: root.draft.spellCheckEnabled = checked
            }

            Binding {
                target: spellingCheck
                property: "checked"
                value: root.draft.spellCheckEnabled
            }

            Repeater {
                model: Settings.availableSpellCheckLanguages()

                delegate: CheckBox {
                    id: languageCheck
                    required property var modelData
                    required property int index
                    Kirigami.FormData.label: index === 0 ? qsTr("Languages:") : ""
                    text: modelData.name
                    enabled: root.draft.spellCheckEnabled
                    onToggled: root.setLanguageEnabled(modelData.code, checked)

                    Binding {
                        target: languageCheck
                        property: "checked"
                        value: root.draft.spellCheckLanguages.indexOf(languageCheck.modelData.code) !== -1
                    }
                }
            }
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: Settings.availableSpellCheckLanguages().length === 0
            type: Kirigami.MessageType.Information
            text: qsTr("No spelling dictionaries are installed.")
        }

        Item { Layout.fillHeight: true }
    }
}
