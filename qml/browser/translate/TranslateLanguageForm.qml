import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Kirigami.FormLayout {
    id: root

    required property TabTranslation translation
    property bool isEditable: true

    function byName(first, second) {
        return first.text.localeCompare(second.text)
    }

    function entriesFor(codes) {
        return codes.map(code => ({ code: code, text: TranslationLibrary.languageName(code) })).sort(byName)
    }

    function sourceEntries() {
        const detected = translation.detectedLanguage
        const others = entriesFor(translation.sourceCodes.filter(code => code !== detected))
        const label = qsTr("%1 (detected)").arg(TranslationLibrary.languageName(detected))
        return [{ code: detected, text: label }, ...others]
    }

    function targetEntries() {
        return entriesFor(translation.targetCodes)
    }

    function syncSelection() {
        fromBox.currentIndex = fromBox.indexOfValue(translation.sourceLanguage)
        toBox.currentIndex = toBox.indexOfValue(translation.targetLanguage)
    }

    Component.onCompleted: syncSelection()

    Connections {
        target: root.translation
        function onLanguagesChanged() { root.syncSelection() }
    }

    ComboBox {
        id: fromBox
        Kirigami.FormData.label: qsTr("From:")
        Layout.fillWidth: true
        enabled: root.isEditable
        model: root.sourceEntries()
        textRole: "text"
        valueRole: "code"
        onActivated: root.translation.setSourceLanguage(currentValue)
    }

    ComboBox {
        id: toBox
        Kirigami.FormData.label: qsTr("To:")
        Layout.fillWidth: true
        enabled: root.isEditable
        model: root.targetEntries()
        textRole: "text"
        valueRole: "code"
        onActivated: root.translation.setTargetLanguage(currentValue)
    }
}
