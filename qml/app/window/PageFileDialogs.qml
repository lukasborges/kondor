import QtQuick
import QtQuick.Dialogs
import QtWebEngine
import Kondor

Item {
    id: root

    required property TabModel tabs

    readonly property bool canPrintOrSave: tabs.currentTab ? !tabs.currentTab.newTabPage : false
    readonly property var pageSaveFormats: [
        WebEngineDownloadRequest.CompleteHtmlSaveFormat,
        WebEngineDownloadRequest.SingleHtmlSaveFormat,
        WebEngineDownloadRequest.MimeHtmlSaveFormat
    ]

    function suggestedFile(extension) {
        return FileHelper.suggestedFileUrl(Settings.downloadDirectory,
                                           tabs.currentTab ? tabs.currentTab.title : "", extension)
    }

    function saveAsPdf() {
        if (!canPrintOrSave)
            return
        pdfDialog.currentFile = suggestedFile(".pdf")
        pdfDialog.open()
    }

    function savePageAs() {
        if (!canPrintOrSave)
            return
        pageDialog.currentFile = suggestedFile(".html")
        pageDialog.open()
    }

    function printPage() {
        if (canPrintOrSave)
            tabs.currentTab.print()
    }

    function exportPdf() {
        if (tabs.currentTab)
            tabs.currentTab.printToPdf(localPath.fromUrl(pdfDialog.selectedFile))
    }

    function savePage() {
        if (!tabs.currentTab)
            return
        const format = pageSaveFormats[pageDialog.selectedNameFilter.index]
        tabs.currentTab.savePage(localPath.fromUrl(pageDialog.selectedFile), format)
    }

    LocalPath { id: localPath }

    FileDialog {
        id: pdfDialog
        title: qsTr("Save as PDF")
        fileMode: FileDialog.SaveFile
        nameFilters: [qsTr("PDF (*.pdf)")]
        defaultSuffix: "pdf"
        onAccepted: root.exportPdf()
    }

    FileDialog {
        id: pageDialog
        title: qsTr("Save Page As")
        fileMode: FileDialog.SaveFile
        nameFilters: [qsTr("Web Page, Complete (*.html)"),
                      qsTr("Web Page, HTML Only (*.html)"),
                      qsTr("Web Archive (*.mhtml)")]
        defaultSuffix: selectedNameFilter.index === 2 ? "mhtml" : "html"
        onAccepted: root.savePage()
    }
}
