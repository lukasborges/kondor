// #349 Multiple profiles — "Manage Profiles" window: one row per profile with Edit and
// Delete buttons, New Profile… under the list and the startup choice below it.
// Twelve profiles and a long name show the scrolling and eliding case.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    width: 520
    height: 560
    color: Kirigami.Theme.backgroundColor

    readonly property var profiles: [
        { name: "Personal", icon: "im-user", running: true },
        { name: "Work", icon: "view-pim-tasks", running: true },
        { name: "Shopping", icon: "globe", running: false },
        { name: "Banking", icon: "favorite", running: false },
        { name: "Games", icon: "games-config-board", running: false },
        { name: "Web Development and Testing of Customer Sites", icon: "code-context", running: false },
        { name: "Home", icon: "go-home", running: false },
        { name: "Travel", icon: "flag", running: false },
        { name: "School", icon: "view-pim-tasks", running: false },
        { name: "News", icon: "globe", running: false },
        { name: "Family", icon: "go-home", running: false },
        { name: "Hobbies", icon: "favorite", running: false }
    ]

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.largeSpacing

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Kirigami.Theme.colorSet: Kirigami.Theme.View
            Kirigami.Theme.inherit: false
            background: Rectangle {
                color: Kirigami.Theme.backgroundColor
                border.color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, Kirigami.Theme.frameContrast)
            }
            ListView {
                clip: true
                currentIndex: 1
                model: profiles
                delegate: ItemDelegate {
                    id: row
                    required property var modelData
                    required property int index
                    width: ListView.view.width
                    highlighted: ListView.isCurrentItem
                    contentItem: RowLayout {
                        spacing: Kirigami.Units.largeSpacing
                        Kirigami.Icon {
                            source: row.modelData.icon
                            Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                            Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                        }
                        Label {
                            text: row.modelData.name
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        ToolButton {
                            icon.name: "document-edit"
                            display: AbstractButton.IconOnly
                            text: "Edit " + row.modelData.name
                            ToolTip.text: "Edit"
                            ToolTip.delay: 600
                        }
                        ToolButton {
                            icon.name: "edit-delete"
                            display: AbstractButton.IconOnly
                            enabled: row.index > 0 && !row.modelData.running
                            text: "Delete " + row.modelData.name
                            ToolTip.text: "Delete…"
                            ToolTip.delay: 600
                        }
                    }
                }
            }
        }

        Button {
            text: "New Profile…"
            icon.name: "list-add"
        }

        Kirigami.FormLayout {
            Layout.fillWidth: true
            ComboBox {
                Kirigami.FormData.label: "At startup:"
                model: ["Ask Every Time", "Personal", "Work", "Shopping"]
                currentIndex: 1
            }
        }

        DialogButtonBox {
            Layout.fillWidth: true
            padding: 0
            standardButtons: DialogButtonBox.Close
        }
    }
}
