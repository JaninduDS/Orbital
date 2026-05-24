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

    // Faint Schrödinger equation in the background — placed behind everything.
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

        // Header: date + countdown
        Text {
            text: AppState.now.toLocaleDateString(Qt.locale(), "dddd MMM d, yyyy")
            color: Theme.text
            font.family: Theme.font
            font.pixelSize: 18
            font.weight: Font.DemiBold
            Layout.fillWidth: true
        }
        Text {
            text: "Orbital · " + AppState.termName
            color: Theme.subtext
            font.family: Theme.mono
            font.pixelSize: 11
            Layout.fillWidth: true
        }

        CountdownRibbon { Layout.fillWidth: true }

        // Section: Today's timeline
        SectionHeader { text: "TODAY" }
        NowStrip { Layout.fillWidth: true; Layout.preferredHeight: 70 }

        // Section: 8-week heatmap
        SectionHeader { text: "WORKLOAD" }
        Heatmap { Layout.fillWidth: true; Layout.preferredHeight: 180 }

        // Section: upcoming tasks
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
            }
        }

        Item { Layout.fillHeight: true }   // spacer
        EnergyBar { Layout.fillWidth: true }
    }

    component SectionHeader: Text {
        color: Theme.overlay0
        font.family: Theme.mono
        font.pixelSize: 10
        font.letterSpacing: 1.5
        topPadding: 6
    }
}
