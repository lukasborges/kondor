import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

RowLayout {
    required property string fileName

    spacing: Kirigami.Units.smallSpacing
    visible: PasswordStore.importPreparing

    BusyIndicator {
        running: parent.visible
    }

    Label {
        Layout.fillWidth: true
        elide: Text.ElideMiddle
        text: qsTr("Reading %1…").arg(parent.fileName)
    }
}
