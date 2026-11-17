import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

RowLayout {
    id: root

    property TabIdentity identity: null

    signal customRequested()

    function syncChoice() {
        if (root.identity)
            combo.currentIndex = choices.indexOf(root.identity.choice)
    }

    function choose(value) {
        if (value === "custom")
            root.customRequested()
        else
            root.identity.choose(value)
    }

    spacing: Kirigami.Units.smallSpacing

    IdentityChoices {
        id: choices
    }

    Connections {
        target: root.identity
        function onChoiceChanged() { root.syncChoice() }
    }

    Kirigami.Icon {
        source: "preferences-web-browser-identification"
        Layout.preferredWidth: Kirigami.Units.iconSizes.small
        Layout.preferredHeight: Kirigami.Units.iconSizes.small
    }

    Label {
        Layout.fillWidth: true
        elide: Text.ElideRight
        text: qsTr("Identify as:")
    }

    ComboBox {
        id: combo
        Layout.preferredWidth: Kirigami.Units.gridUnit * 9
        model: choices.choices
        textRole: "text"
        valueRole: "value"
        Component.onCompleted: root.syncChoice()
        onActivated: root.choose(currentValue)
        Accessible.name: qsTr("Identify as:")
    }
}
