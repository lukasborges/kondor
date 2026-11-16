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

            CheckBox {
                id: sleepCheck
                objectName: "sleepCheck"
                Kirigami.FormData.label: qsTr("Memory:")
                text: qsTr("Put inactive tabs to sleep")
                onToggled: root.draft.tabSleepEnabled = checked
            }

            Binding {
                target: sleepCheck
                property: "checked"
                value: root.draft.tabSleepEnabled
            }

            ComboBox {
                id: sleepAfterCombo
                objectName: "sleepAfterCombo"
                Kirigami.FormData.label: qsTr("Sleep after:")
                enabled: root.draft.tabSleepEnabled
                textRole: "text"
                valueRole: "minutes"
                readonly property int minutesIndex: count > 0 ? indexOfValue(root.draft.tabSleepMinutes) : -1
                model: [
                    { text: qsTr("%n minute(s)", "", 15), minutes: 15 },
                    { text: qsTr("%n minute(s)", "", 30), minutes: 30 },
                    { text: qsTr("%n hour(s)", "", 1), minutes: 60 },
                    { text: qsTr("%n hour(s)", "", 2), minutes: 120 },
                    { text: qsTr("%n hour(s)", "", 4), minutes: 240 }
                ]
                onActivated: root.draft.tabSleepMinutes = currentValue
            }

            Binding {
                target: sleepAfterCombo
                property: "currentIndex"
                value: sleepAfterCombo.minutesIndex
            }
        }

        Item { Layout.fillHeight: true }
    }
}
