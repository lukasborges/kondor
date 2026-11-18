import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import QtCore
import org.kde.kirigami as Kirigami
import Kondor

Dialog {
    id: root

    property Tab tab: null
    property var grabResult: null
    property bool isCapturing: false
    property bool isFullPage: false
    property bool hasCopied: false

    anchors.centerIn: Overlay.overlay
    width: Kirigami.Units.gridUnit * 30
    modal: true
    title: qsTr("Take Screenshot")
    closePolicy: Popup.CloseOnEscape

    function openForTab(targetTab) {
        tab = targetTab
        isFullPage = false
        open()
    }

    function capture() {
        grabResult = null
        isCapturing = true
        tab.captureScreenshot(isFullPage)
    }

    function copyImage() {
        Screenshot.copyToClipboard(grabResult.image)
        hasCopied = true
        copiedTimer.restart()
    }

    function chooseFileToSave() {
        saveDialog.currentFile = Screenshot.suggestedFileUrl(
            StandardPaths.writableLocation(StandardPaths.PicturesLocation), tab.title)
        saveDialog.open()
    }

    function saveTo(url) {
        if (grabResult.saveToFile(localPath.fromUrl(url)))
            close()
        else
            Notifier.notify(qsTr("Saving the screenshot failed"), localPath.fromUrl(url), "document-save")
    }

    function receive(result) {
        grabResult = result
        isCapturing = false
    }

    onAboutToShow: capture()
    onAboutToHide: { grabResult = null; hasCopied = false }

    LocalPath { id: localPath }

    Timer {
        id: copiedTimer
        interval: 2000
        onTriggered: root.hasCopied = false
    }

    Connections {
        target: root.tab
        function onScreenshotCaptured(result) { root.receive(result) }
    }

    FileDialog {
        id: saveDialog
        title: qsTr("Save Screenshot")
        fileMode: FileDialog.SaveFile
        nameFilters: [qsTr("PNG Image (*.png)")]
        defaultSuffix: "png"
        onAccepted: root.saveTo(selectedFile)
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        ScreenshotModeButtons {
            Layout.alignment: Qt.AlignHCenter
            isFullPage: root.isFullPage
            onModeChosen: function(fullPage) {
                root.isFullPage = fullPage
                root.capture()
            }
        }

        ScreenshotPreview {
            Layout.fillWidth: true
            grabResult: root.grabResult
            isCapturing: root.isCapturing
        }
    }

    footer: DialogButtonBox {
        Button {
            text: qsTr("Copy")
            icon.name: root.hasCopied ? "checkmark" : "edit-copy"
            enabled: root.grabResult !== null
            ToolTip.visible: root.hasCopied
            ToolTip.text: qsTr("Copied")
            DialogButtonBox.buttonRole: DialogButtonBox.ActionRole
            onClicked: root.copyImage()
        }
        Button {
            text: qsTr("Save…")
            icon.name: "document-save"
            highlighted: true
            enabled: root.grabResult !== null
            DialogButtonBox.buttonRole: DialogButtonBox.ActionRole
            onClicked: root.chooseFileToSave()
        }
        Button {
            text: qsTr("Close")
            icon.name: "dialog-close"
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
        }
    }
}
