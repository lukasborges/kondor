import QtQuick
import Kondor

QtObject {
    id: root

    property var passwords: ({})

    function keyOf(origin, username) {
        return origin + "\n" + username
    }

    function isRevealed(origin, username) {
        return root.passwords[root.keyOf(origin, username)] !== undefined
    }

    function passwordOf(origin, username) {
        return root.passwords[root.keyOf(origin, username)]
    }

    function toggleReveal(origin, username) {
        const copy = Object.assign({}, root.passwords)
        const key = root.keyOf(origin, username)
        if (copy[key] !== undefined)
            delete copy[key]
        else
            copy[key] = PasswordStore.password(origin, username)
        root.passwords = copy
    }

    function clear() {
        root.passwords = ({})
    }
}
