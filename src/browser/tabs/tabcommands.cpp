#include "browser/tab.h"

void Tab::goBack()
{
    emit backRequested();
}

void Tab::goForward()
{
    emit forwardRequested();
}

void Tab::reload()
{
    emit reloadRequested();
}

void Tab::stop()
{
    emit stopRequested();
}

void Tab::zoomIn()
{
    emit zoomInRequested();
}

void Tab::zoomOut()
{
    emit zoomOutRequested();
}

void Tab::resetZoom()
{
    emit resetZoomRequested();
}

void Tab::find(const QString &text, bool backward, bool caseSensitive)
{
    emit findRequested(text, backward, caseSensitive);
}

void Tab::stopFind()
{
    emit stopFindRequested();
}

void Tab::focusPage()
{
    emit focusPageRequested();
}

void Tab::toggleDevTools()
{
    emit toggleDevToolsRequested();
}

void Tab::printToPdf(const QString &filePath)
{
    emit printToPdfRequested(filePath);
}

void Tab::print()
{
    emit printRequested();
}

void Tab::savePage(const QString &filePath, int format)
{
    emit savePageRequested(filePath, format);
}

void Tab::setPdfFinished(const QString &filePath, bool success)
{
    emit pdfFinished(filePath, success);
}

void Tab::inspectElement()
{
    emit inspectElementRequested();
}

void Tab::closeTab()
{
    emit closeRequested();
}

void Tab::openTab(const QUrl &url, bool background)
{
    emit openTabRequested(url, background);
}

void Tab::selectNeighborTab(int delta)
{
    emit neighborTabRequested(delta);
}

void Tab::downloadUrl(const QUrl &url, const QString &fileName)
{
    emit downloadUrlRequested(url, fileName);
}
