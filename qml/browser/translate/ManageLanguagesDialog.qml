import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Dialog {
    id: root

    anchors.centerIn: Overlay.overlay
    width: 460
    modal: true
    title: qsTr("Manage Languages")
    standardButtons: Dialog.Close
    onAboutToShow: TranslationLibrary.refresh()

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.smallSpacing

        Repeater {
            model: TranslationLibrary.installed
            delegate: ManageLanguageRow { Layout.fillWidth: true }
        }

        Kirigami.PlaceholderMessage {
            Layout.fillWidth: true
            visible: TranslationLibrary.installed.length === 0
            text: qsTr("No languages downloaded")
        }
    }
}
