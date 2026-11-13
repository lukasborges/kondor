import QtQuick
import QtWebEngine
import Kondor

Item {
    id: root

    required property Tab tab
    required property WebEngineView webView

    property string printPath: ""

    visible: false

    function notifyPrintFailed() {
        Notifier.notify(qsTr("Print failed"), tab.title, "document-print")
    }

    function finishPrint(filePath, success) {
        printPath = ""
        if (success)
            FileHelper.openFile(filePath)
        else
            notifyPrintFailed()
    }

    function notifySavedPdf(filePath, success) {
        if (success)
            Notifier.notify(qsTr("PDF saved"), filePath, "document-export")
        else
            Notifier.notify(qsTr("Saving the PDF failed"), filePath, "document-export")
    }

    function pdfFinished(filePath, success) {
        tab.setPdfFinished(filePath, success)
        if (filePath === printPath)
            finishPrint(filePath, success)
        else
            notifySavedPdf(filePath, success)
    }

    function printToPdf(filePath) {
        webView.printToPdf(filePath, WebEngineView.A4, WebEngineView.Portrait)
    }

    function printViaTemporaryPdf() {
        const path = FileHelper.tempPdfPath()
        if (path === "")
            return notifyPrintFailed()
        printPath = path
        printToPdf(path)
    }

    Connections {
        target: root.tab
        function onPrintToPdfRequested(filePath) { root.printToPdf(filePath) }
        function onPrintRequested() { root.printViaTemporaryPdf() }
        function onSavePageRequested(filePath, format) { root.webView.save(filePath, format) }
    }
}
