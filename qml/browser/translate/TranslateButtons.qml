import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

RowLayout {
    id: root

    required property TabTranslation translation

    signal dismissed()

    readonly property bool isOffer: translation.state === "idle" || translation.state === "error"

    Layout.alignment: Qt.AlignRight
    spacing: Kirigami.Units.smallSpacing

    Button {
        visible: root.isOffer
        text: qsTr("Not Now")
        onClicked: root.dismissed()
    }

    Button {
        visible: root.translation.state === "downloading"
        text: qsTr("Cancel")
        icon.name: "dialog-cancel"
        onClicked: root.translation.cancel()
    }

    Button {
        visible: root.translation.state === "translated"
        text: qsTr("Show Original")
        icon.name: "edit-undo"
        onClicked: root.translation.showOriginal()
    }

    Button {
        visible: root.isOffer
        text: root.translation.state === "error" ? qsTr("Try Again") : qsTr("Translate")
        icon.name: "translate"
        highlighted: true
        onClicked: root.translation.translate()
    }
}
