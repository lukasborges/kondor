import QtQuick

QtObject {
    readonly property var choices: [
        { value: "kondor", text: qsTr("Kondor (default)") },
        { value: "firefox", text: qsTr("Firefox") },
        { value: "chrome", text: qsTr("Chrome") },
        { value: "custom", text: qsTr("Custom…") }
    ]

    function indexOf(value) {
        return choices.findIndex(choice => choice.value === value)
    }

    function nameOf(value) {
        const choice = choices[indexOf(value)]
        return choice ? choice.text : ""
    }
}
