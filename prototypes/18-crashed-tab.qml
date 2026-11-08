// #18 Crashed page — página sobreposta quando o processo de renderização morre.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    tabs: [{ title: "KDE Community", icon: "dialog-error" }, { title: "Planet KDE", icon: "internet-web-browser" }]
    Rectangle {
        anchors.fill: parent
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor
        ColumnLayout {
            anchors.centerIn: parent
            width: 480
            spacing: Kirigami.Units.largeSpacing * 2
            Kirigami.Icon { source: "dialog-error"; Layout.preferredWidth: 64; Layout.preferredHeight: 64; Layout.alignment: Qt.AlignHCenter }
            Kirigami.Heading { level: 2; text: "Esta aba travou"; Layout.alignment: Qt.AlignHCenter }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                text: "O processo da página foi encerrado, talvez por falta de memória. As outras abas não foram afetadas."
            }
            Label { text: "Código de saída: 9"; color: Kirigami.Theme.disabledTextColor; font: Kirigami.Theme.smallFont; Layout.alignment: Qt.AlignHCenter }
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: Kirigami.Units.largeSpacing
                Button { text: "Fechar aba"; icon.name: "tab-close" }
                Button { text: "Recarregar"; icon.name: "view-refresh"; highlighted: true }
            }
        }
    }
}
