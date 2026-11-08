// Página web falsa (genérica) para preencher a área de conteúdo dos protótipos.
// heading/paragraphs aceitam rich text: <mark>palavra</mark> vira destaque de busca
// e <cur>palavra</cur> o destaque da ocorrência atual.
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    id: page
    property string heading: "Plasma 6: o desktop da comunidade KDE"
    property var paragraphs: [
        "O Plasma é o ambiente de trabalho desenvolvido pela comunidade KDE. Ele é leve, rápido e totalmente configurável, do painel aos atalhos de teclado.",
        "Com o Plasma 6, toda a pilha foi portada para o Qt 6 e para o KDE Frameworks 6, trazendo Wayland como sessão padrão, HDR e melhorias de acessibilidade."
    ]
    property var paragraphsAfter: [
        "Aplicativos como Dolphin, Konsole, Kate e Okular seguem as mesmas diretrizes de interface (HIG) e o tema Breeze, criando uma experiência consistente."
    ]
    property bool showHero: true
    anchors.fill: parent
    color: "#ffffff"

    function rich(s) {
        return s.replace(/<mark>/g, "<span style='background-color:#fdbc4b'>")
                .replace(/<cur>/g, "<span style='background-color:#f67400;color:#ffffff'>")
                .replace(/<\/(mark|cur)>/g, "</span>")
    }

    Rectangle {
        id: siteHeader
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: 56
        color: "#232629"
        Row {
            anchors.verticalCenter: parent.verticalCenter
            x: 40
            spacing: 28
            Kirigami.Icon { source: "kde"; width: 28; height: 28; anchors.verticalCenter: parent.verticalCenter }
            Repeater {
                model: ["Produtos", "Comunidade", "Doar", "Notícias"]
                Text { text: modelData; color: "#fcfcfc"; font.pixelSize: 14; anchors.verticalCenter: parent.verticalCenter }
            }
        }
    }

    ColumnLayout {
        anchors { left: parent.left; top: siteHeader.bottom; leftMargin: 80; topMargin: 32 }
        width: Math.min(640, page.width - 160)
        spacing: 14
        Text {
            Layout.fillWidth: true
            text: page.rich(page.heading)
            textFormat: Text.RichText
            font.pixelSize: 30; font.bold: true; color: "#232629"
            wrapMode: Text.WordWrap
        }
        Repeater {
            model: page.paragraphs
            Text {
                Layout.fillWidth: true
                text: page.rich(modelData)
                textFormat: Text.RichText
                font.pixelSize: 15; color: "#31363b"; lineHeight: 1.35
                wrapMode: Text.WordWrap
            }
        }
        Rectangle {
            visible: page.showHero
            Layout.fillWidth: true
            Layout.preferredHeight: 150
            radius: 6
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: "#3daee9" }
                GradientStop { position: 1; color: "#1d78b5" }
            }
            Kirigami.Icon { anchors.centerIn: parent; source: "plasma"; width: 64; height: 64 }
        }
        Repeater {
            model: page.paragraphsAfter
            Text {
                Layout.fillWidth: true
                text: page.rich(modelData)
                textFormat: Text.RichText
                font.pixelSize: 15; color: "#31363b"; lineHeight: 1.35
                wrapMode: Text.WordWrap
            }
        }
    }
}
