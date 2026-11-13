import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ColumnLayout {
    spacing: 0
    visible: PasswordStore.importRunning

    Kirigami.InlineMessage {
        Layout.fillWidth: true
        visible: true
        type: Kirigami.MessageType.Information
        text: qsTr("Importing passwords… %1 of %2 sites")
              .arg(PasswordStore.importDone).arg(PasswordStore.importTotal)
    }

    ProgressBar {
        Layout.fillWidth: true
        from: 0
        to: PasswordStore.importTotal
        value: PasswordStore.importDone
    }
}
