import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Grid {
    id: picker

    property string current: "floating"

    signal chosen(string style)

    readonly property var styles: [
        { id: "floating", name: qsTr("Floating") },
        { id: "below", name: qsTr("Below Address Bar") },
        { id: "classic", name: qsTr("Classic") }
    ]

    columns: 2
    spacing: Kirigami.Units.largeSpacing

    function focusStyleAt(index) {
        const target = repeater.itemAt(Math.max(0, Math.min(index, styles.length - 1)))
        if (target)
            target.forceActiveFocus(Qt.TabFocusReason)
    }

    Repeater {
        id: repeater
        model: picker.styles

        delegate: ItemDelegate {
            id: option

            required property var modelData
            required property int index
            readonly property bool isSelected: modelData.id === picker.current

            highlighted: isSelected
            activeFocusOnTab: isSelected
            padding: Kirigami.Units.smallSpacing
            Accessible.name: modelData.name
            Accessible.role: Accessible.RadioButton
            Accessible.checked: isSelected
            onClicked: picker.chosen(modelData.id)
            Keys.onReturnPressed: clicked()
            Keys.onEnterPressed: clicked()
            Keys.onLeftPressed: picker.focusStyleAt(index - 1)
            Keys.onRightPressed: picker.focusStyleAt(index + 1)
            Keys.onUpPressed: picker.focusStyleAt(index - picker.columns)
            Keys.onDownPressed: picker.focusStyleAt(index + picker.columns)

            contentItem: ColumnLayout {
                spacing: Kirigami.Units.smallSpacing

                TabStyleThumbnail {
                    tabStyle: option.modelData.id
                    Layout.alignment: Qt.AlignHCenter
                }

                Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: option.modelData.name
                    elide: Text.ElideRight
                }
            }
        }
    }
}
