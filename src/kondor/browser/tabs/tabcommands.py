from PySide6.QtCore import QObject, QUrl, Signal, Slot


class TabCommands(QObject):
    navigationRequested = Signal(QUrl)
    newTabPageRequested = Signal()
    backRequested = Signal()
    forwardRequested = Signal()
    reloadRequested = Signal()
    reloadBypassingCacheRequested = Signal()
    stopRequested = Signal()
    zoomInRequested = Signal()
    zoomOutRequested = Signal()
    resetZoomRequested = Signal()
    findRequested = Signal(str, bool, bool)
    stopFindRequested = Signal()
    focusPageRequested = Signal()
    exitFullScreenRequested = Signal()
    toggleDevToolsRequested = Signal()
    toggleReaderModeRequested = Signal()
    printToPdfRequested = Signal(str)
    printRequested = Signal()
    savePageRequested = Signal(str, int)
    pdfFinished = Signal(str, bool)
    inspectElementRequested = Signal()
    closeRequested = Signal()
    openTabRequested = Signal(QUrl, bool)
    neighborTabRequested = Signal(int)
    downloadUrlRequested = Signal(QUrl, str)

    @Slot()
    def goBack(self) -> None:
        self.backRequested.emit()

    @Slot()
    def goForward(self) -> None:
        self.forwardRequested.emit()

    @Slot()
    def reload(self) -> None:
        self.reloadRequested.emit()

    @Slot()
    def reloadBypassingCache(self) -> None:
        self.reloadBypassingCacheRequested.emit()

    @Slot()
    def stop(self) -> None:
        self.stopRequested.emit()

    @Slot()
    def zoomIn(self) -> None:
        self.zoomInRequested.emit()

    @Slot()
    def zoomOut(self) -> None:
        self.zoomOutRequested.emit()

    @Slot()
    def resetZoom(self) -> None:
        self.resetZoomRequested.emit()

    @Slot(str, bool, bool)
    def find(self, text: str, backward: bool, case_sensitive: bool) -> None:
        self.findRequested.emit(text, backward, case_sensitive)

    @Slot()
    def stopFind(self) -> None:
        self.stopFindRequested.emit()

    @Slot()
    def focusPage(self) -> None:
        self.focusPageRequested.emit()

    @Slot()
    def toggleDevTools(self) -> None:
        self.toggleDevToolsRequested.emit()

    @Slot(str)
    def printToPdf(self, file_path: str) -> None:
        self.printToPdfRequested.emit(file_path)

    @Slot()
    def print(self) -> None:
        self.printRequested.emit()

    @Slot(str, int)
    def savePage(self, file_path: str, page_format: int) -> None:
        self.savePageRequested.emit(file_path, page_format)

    @Slot(str, bool)
    def setPdfFinished(self, file_path: str, success: bool) -> None:
        self.pdfFinished.emit(file_path, success)

    @Slot()
    def inspectElement(self) -> None:
        self.inspectElementRequested.emit()

    @Slot()
    def closeTab(self) -> None:
        self.closeRequested.emit()

    @Slot(QUrl, bool)
    def openTab(self, url: QUrl, background: bool) -> None:
        self.openTabRequested.emit(url, background)

    @Slot(int)
    def selectNeighborTab(self, delta: int) -> None:
        self.neighborTabRequested.emit(delta)

    @Slot(QUrl, str)
    def downloadUrl(self, url: QUrl, file_name: str) -> None:
        self.downloadUrlRequested.emit(url, file_name)
