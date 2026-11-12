import QtQuick
import QtWebEngine
import Kondor

QtObject {
    id: root

    required property var request
    required property WebEngineView webView
    required property Tab tab
    required property TabModel tabModel

    readonly property var webActions: ({
        "copyLink": WebEngineView.CopyLinkToClipboard,
        "saveLink": WebEngineView.DownloadLinkToDisk,
        "saveImage": WebEngineView.DownloadImageToDisk,
        "copyImage": WebEngineView.CopyImageToClipboard,
        "copyImageAddress": WebEngineView.CopyImageUrlToClipboard,
        "saveMedia": WebEngineView.DownloadMediaToDisk,
        "copyMediaAddress": WebEngineView.CopyMediaUrlToClipboard,
        "toggleMediaControls": WebEngineView.ToggleMediaControls,
        "toggleMediaLoop": WebEngineView.ToggleMediaLoop,
        "copySelection": WebEngineView.Copy,
        "undo": WebEngineView.Undo,
        "redo": WebEngineView.Redo,
        "cut": WebEngineView.Cut,
        "paste": WebEngineView.Paste,
        "pastePlain": WebEngineView.PasteAndMatchStyle,
        "selectAll": WebEngineView.SelectAll,
        "viewSource": WebEngineView.ViewSource
    })

    readonly property var customActions: ({
        "openLinkNewTab": root.openLinkNewTab,
        "openLinkNewPrivateTab": root.openLinkNewPrivateTab,
        "openImageNewTab": root.openImageNewTab,
        "searchSelection": root.searchSelection,
        "replaceMisspelling": root.replaceMisspelling,
        "back": root.goBack,
        "forward": root.goForward,
        "reload": root.reload,
        "inspectElement": root.inspectElement
    })

    function perform(action, data) {
        if (action in webActions)
            webView.triggerWebAction(webActions[action])
        else if (action in customActions)
            customActions[action](data)
    }

    function openInNewTab(url) {
        tabModel.addTabWithProfile(tab.profile, url, false)
    }

    function openLinkNewTab(data) {
        openInNewTab(request.linkUrl)
    }

    function openLinkNewPrivateTab(data) {
        tabModel.addTab(true, request.linkUrl)
    }

    function openImageNewTab(data) {
        openInNewTab(request.mediaUrl)
    }

    function searchSelection(data) {
        openInNewTab(ProfileManager.resolveAddress(request.selectedText))
    }

    function replaceMisspelling(word) {
        webView.replaceMisspelledWord(word)
    }

    function goBack(data) {
        webView.goBack()
    }

    function goForward(data) {
        webView.goForward()
    }

    function reload(data) {
        webView.reload()
    }

    function inspectElement(data) {
        tab.inspectElement()
    }
}
