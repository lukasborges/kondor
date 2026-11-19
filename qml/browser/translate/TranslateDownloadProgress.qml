import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ColumnLayout {
    id: root

    required property TabTranslation translation

    spacing: Kirigami.Units.smallSpacing

    ProgressBar {
        Layout.fillWidth: true
        from: 0
        to: 1
        value: root.translation.progress
    }

    Label {
        Layout.fillWidth: true
        text: qsTr("Downloading %1: %2 of %3 MB").arg(root.translation.downloadLabel)
            .arg(root.translation.downloadedMegabytes).arg(root.translation.totalMegabytes)
        color: Kirigami.Theme.disabledTextColor
        font: Kirigami.Theme.smallFont
        elide: Text.ElideRight
    }
}
