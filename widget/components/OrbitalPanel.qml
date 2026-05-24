// The main panel: stacks all sections vertically.
import QtQuick
import QtQuick.Layouts
import "."

Rectangle {
    id: panel
    color: Theme.mantle
    radius: Theme.radius
    border.color: Theme.surface0
    border.width: 1
    clip: true

    signal closeRequested()

    Text {
        anchors.centerIn: parent
        text: "iℏ ∂ψ/∂t = Ĥψ"
        color: Theme.text
        opacity: 0.05
        font.family: Theme.mono
        font.pixelSize: 64
        rotation: -20
        z: -1
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Theme.pad
        spacing: Theme.gap

        // Header row: title block + close button
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0
                Text {
                    text: AppState.now.toLocaleDateString(Qt.locale(), "dddd MMM d, yyyy")
                    color: Theme.text
                    font.family: Theme.font
                    font.pixelSize: 17
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
                Text {
                    text: "Orbital · " + AppState.termName
                    color: Theme.subtext
                    font.family: Theme.mono
                    font.pixelSize: 10
                    Layout.fillWidth: true
                }
            }

            Rectangle {
                id: closeBtn
                Layout.preferredWidth: 22
                Layout.preferredHeight: 22
                radius: 11
                color: closeMa.containsMouse ? Theme.red : Theme.surface0
                Behavior on color { ColorAnimation { duration: 120 } }
                Text {
                    anchors.centerIn: parent
                    text: "×"
                    color: Theme.text
                    font.family: Theme.font
                    font.pixelSize: 16
                    font.weight: Font.Bold
                }
                MouseArea {
                    id: closeMa
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: panel.closeRequested()
                }
            }
        }

        CountdownRibbon { Layout.fillWidth: true }

        SectionHeader { text: "TODAY" }
        NowStrip { Layout.fillWidth: true; Layout.preferredHeight: 64 }

        SectionHeader { text: "WORKLOAD" }
        Heatmap { Layout.fillWidth: true }

        SectionHeader { text: "NEXT UP" }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6
            Repeater {
                model: AppState.nextTasks
                TaskCard {
                    Layout.fillWidth: true
                    taskData: modelData
                }
            }
            Text {
                visible: AppState.nextTasks.length === 0
                text: AppState.error || "No upcoming tasks"
                color: AppState.error ? Theme.red : Theme.subtext
                font.family: Theme.font
                font.pixelSize: 12
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }

        Item { Layout.fillHeight: true }
        EnergyBar { Layout.fillWidth: true }
    }

    component SectionHeader: Text {
        color: Theme.overlay0
        font.family: Theme.mono
        font.pixelSize: 10
        font.letterSpacing: 1.5
        topPadding: 4
    }
}
