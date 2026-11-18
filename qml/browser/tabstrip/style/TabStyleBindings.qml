import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami

Item {
    id: bindings

    required property var control

    Binding {
        when: bindings.control.isStyled && !bindings.control.tab.pinned
        target: bindings.control
        property: "leftPadding"
        value: Kirigami.Units.smallSpacing * 2
    }

    Binding {
        when: bindings.control.isStyled && !bindings.control.tab.pinned
        target: bindings.control
        property: "rightPadding"
        value: Kirigami.Units.smallSpacing
    }

    Binding {
        target: bindings.control.background
        property: "visible"
        value: !bindings.control.isStyled
    }

    Binding {
        when: bindings.control.isStyled
        target: bindings.control
        property: "implicitHeight"
        value: Kirigami.Units.gridUnit * 2
    }
}
