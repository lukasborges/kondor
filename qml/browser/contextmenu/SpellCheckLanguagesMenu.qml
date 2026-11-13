import QtQuick
import QtQuick.Controls
import Kondor

Menu {
    id: root

    title: qsTr("Spell Check Languages")
    icon.name: "tools-check-spelling"
    popupType: Popup.Item

    function toggleSpellCheckLanguage(code, enabled) {
        const others = Settings.spellCheckLanguages.filter(function(c) { return c !== code })
        Settings.spellCheckLanguages = enabled ? others.concat([code]) : others
    }

    function addLanguage(language) {
        addItem(languageItemComponent.createObject(null, {
            "text": language.name,
            "code": language.code,
            "checked": Settings.spellCheckLanguages.indexOf(language.code) !== -1
        }))
    }

    Component.onCompleted: Settings.availableSpellCheckLanguages().forEach(addLanguage)

    Component {
        id: languageItemComponent

        MenuItem {
            property string code
            checkable: true
            onToggled: root.toggleSpellCheckLanguage(code, checked)
        }
    }
}
