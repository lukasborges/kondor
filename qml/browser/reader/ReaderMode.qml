import QtQuick
import QtWebEngine
import Kondor

Item {
    id: root

    required property Tab tab
    required property WebEngineView webView
    required property ReaderStyle style

    property url readerOriginalUrl: ""
    property bool readerLoadPending: false

    readonly property string readabilityCall: "\n;(function() {"
        + "const a = new Readability(document.cloneNode(true)).parse();"
        + "return a ? { title: a.title, byline: a.byline, content: a.content,"
        + " siteName: a.siteName, lang: a.lang, dir: a.dir } : null; })();"

    visible: false

    function readResource(name) {
        return FileHelper.readerResource(name)
    }

    function escapeHtml(text) {
        return String(text ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;")
            .replace(/>/g, "&gt;").replace(/"/g, "&quot;")
    }

    function detectReader() {
        webView.runJavaScript(
            readResource("Readability-readerable.js")
                + "\n;isProbablyReaderable(document);",
            WebEngineScript.ApplicationWorld,
            function(result) { root.tab.setReaderAvailable(result === true) })
    }

    function enterReader() {
        const original = webView.url
        runReadability(function(article) { root.showArticle(article, original) })
    }

    function runReadability(callback) {
        webView.runJavaScript(readResource("Readability.js") + readabilityCall,
                              WebEngineScript.ApplicationWorld, callback)
    }

    function isUsableArticle(article, original) {
        return Boolean(article && article.content) && webView.url === original
    }

    function showArticle(article, original) {
        if (!isUsableArticle(article, original)) {
            tab.setReaderAvailable(false)
            return
        }
        loadArticle(buildHtml(article), original)
    }

    function articleValues(article) {
        return {
            lang: escapeHtml(article.lang || ""),
            dir: escapeHtml(article.dir || "ltr"),
            title: escapeHtml(article.title),
            siteName: escapeHtml(article.siteName),
            byline: escapeHtml(article.byline),
            vars: style.readerVars(),
            content: article.content
        }
    }

    function buildHtml(article) {
        const values = articleValues(article)
        return readResource("template.html")
            .replace(/\{\{(\w+)\}\}/g, function(match, key) { return values[key] ?? "" })
    }

    function loadArticle(html, original) {
        readerOriginalUrl = original
        readerLoadPending = true
        tab.setReaderActive(true)
        webView.loadHtml(html, original)
    }

    function exitReader() {
        if (!tab.readerActive)
            return
        const original = readerOriginalUrl
        readerLoadPending = false
        tab.setReaderActive(false)
        webView.url = original
    }

    function endReaderOnNavigation() {
        if (!tab.readerActive)
            return tab.setReaderAvailable(false)
        if (readerLoadPending)
            return
        tab.setReaderActive(false)
        tab.setReaderAvailable(false)
    }

    function updateOnLoad(status) {
        if (status === WebEngineLoadingInfo.LoadStartedStatus)
            endReaderOnNavigation()
        else if (tab.readerActive)
            readerLoadPending = false
    }

    Connections {
        target: root.tab
        function onToggleReaderModeRequested() {
            if (root.tab.readerActive)
                root.exitReader()
            else
                root.enterReader()
        }
    }
}
