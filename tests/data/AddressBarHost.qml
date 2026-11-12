import QtQuick
import QtQuick.Controls
import Kondor

ApplicationWindow {
    id: window
    width: 800
    height: 300
    visible: true

    property var tabModel
    property alias addressBar: bar

    function openUrl(url, background) {}

    AddressBar {
        id: bar
        width: 700
        tabs: window.tabModel
        browserWindow: window
    }
}
