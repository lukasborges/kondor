import org.kde.kirigami as Kirigami

Kirigami.ListSectionHeader {
    required property int windowNumber

    text: windowNumber === 1 ? qsTr("This Window") : qsTr("Window %1").arg(windowNumber)
}
