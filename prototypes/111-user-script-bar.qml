// #111 User scripts — a .user.js page offers to install the script (InlineBar above the page).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    address: "https://example.org/scripts/wide-github.user.js"
    tabs: [{ title: "wide-github.user.js", icon: "text-x-javascript" }]
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    belowHeader: [
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            position: Kirigami.InlineMessage.Position.Header
            visible: true
            type: Kirigami.MessageType.Information
            icon.name: "text-x-javascript"
            showCloseButton: true
            text: "This page is a user script."
            actions: [
                Kirigami.Action { text: "Install…"; icon.name: "download" }
            ]
        }
    ]
    Rectangle {
        anchors.fill: parent
        color: "#ffffff"
        Text {
            x: 8; y: 8
            font.family: "monospace"
            font.pixelSize: 13
            color: "#232629"
            text: "// ==UserScript==\n"
                + "// @name         Wide GitHub\n"
                + "// @namespace    https://example.org/scripts\n"
                + "// @version      1.4.2\n"
                + "// @description  Uses the full window width on GitHub.\n"
                + "// @author       Jane Example\n"
                + "// @match        https://github.com/*\n"
                + "// @match        https://gist.github.com/*\n"
                + "// @grant        GM.addStyle\n"
                + "// @grant        GM.notification\n"
                + "// @grant        GM_xmlhttpRequest\n"
                + "// @updateURL    https://example.org/scripts/wide-github.meta.js\n"
                + "// ==/UserScript==\n\n"
                + "GM.addStyle(\".container-xl { max-width: none !important; }\");\n"
        }
    }
}
