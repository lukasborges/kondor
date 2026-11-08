// #4 Download manager — botão na barra (com progresso) e popup com a lista de downloads.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    toolbarExtras: [
        ToolButton {
            icon.name: "download"
            display: AbstractButton.IconOnly
            checked: true
            ProgressBar {
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 4 }
                height: 3
                value: 0.42
            }
        }
    ]
    FakePage {}

    Popup {
        popupType: Popup.Item
        x: frame.width - width - 40
        y: -2
        width: 440
        padding: 0
        Component.onCompleted: open()
        contentItem: ColumnLayout {
            spacing: 0
            Repeater {
                model: [
                    { n: "Fedora-KDE-Live-x86_64-43.iso", m: "application-x-cd-image", p: 0.42, s: "1,1 GB de 2,6 GB — 18,4 MB/s — 1 min restante", st: "run" },
                    { n: "relatorio-anual.pdf", m: "application-pdf", p: 1, s: "Concluído — 2,3 MB", st: "done" },
                    { n: "kondor-0.1.5.tar.gz", m: "application-x-compressed-tar", p: 0.65, s: "Pausado — 3,4 MB de 5,2 MB", st: "paused" },
                    { n: "imagem.png", m: "image-png", p: 0.1, s: "Cancelado", st: "cancel" }
                ]
                delegate: ItemDelegate {
                    required property var modelData
                    Layout.fillWidth: true
                    padding: Kirigami.Units.largeSpacing
                    contentItem: RowLayout {
                        spacing: Kirigami.Units.largeSpacing
                        Kirigami.Icon { source: modelData.m; Layout.preferredWidth: 32; Layout.preferredHeight: 32 }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label { text: modelData.n; elide: Text.ElideMiddle; Layout.fillWidth: true }
                            ProgressBar { visible: modelData.st === "run" || modelData.st === "paused"; value: modelData.p; Layout.fillWidth: true }
                            Label {
                                text: modelData.s
                                font: Kirigami.Theme.smallFont
                                color: modelData.st === "cancel" ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.disabledTextColor
                            }
                        }
                        ToolButton {
                            visible: modelData.st === "run" || modelData.st === "paused"
                            icon.name: modelData.st === "run" ? "media-playback-pause" : "media-playback-start"
                            display: AbstractButton.IconOnly
                        }
                        ToolButton {
                            icon.name: modelData.st === "done" ? "folder-open" : (modelData.st === "cancel" ? "view-refresh" : "dialog-cancel")
                            display: AbstractButton.IconOnly
                        }
                    }
                }
            }
            Kirigami.Separator { Layout.fillWidth: true }
            RowLayout {
                Layout.fillWidth: true
                Layout.margins: Kirigami.Units.smallSpacing
                Button { text: "Abrir pasta de downloads"; icon.name: "folder-download"; flat: true }
                Item { Layout.fillWidth: true }
                Button { text: "Limpar concluídos"; icon.name: "edit-clear-history"; flat: true }
            }
        }
    }
}
