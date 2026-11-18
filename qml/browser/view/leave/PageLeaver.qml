import QtQuick
import QtWebEngine
import Kondor

QtObject {
    required property Tab tab
    required property TabModel tabModel
    required property WebEngineView webView

    function leave() {
        if (webView.canGoBack)
            webView.goBack()
        else if (tabModel.count > 1)
            tabModel.closeTabObject(tab)
        else
            tab.showNewTabPage()
    }
}
