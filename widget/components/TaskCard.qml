// One upcoming task. Click to toggle in-progress (writes back via Process).
import QtQuick
import Quickshell.Io
import "."

Rectangle {
    id: card
    property var taskData: ({})
    implicitHeight: 54
    radius: 6
    color: ma.containsMouse ? Theme.surface1 : Theme.surface0
    Behavior on color { ColorAnimation { duration: 120 } }

    // Course color stripe
    Rectangle {
        width: 4
        height: parent.height - 8
        anchors.left: parent.left
        anchors.leftMargin: 4
        anchors.verticalCenter: parent.verticalCenter
        radius: 2
        color: card.taskData.color || Theme.overlay0
    }

    Column {
        anchors.left: parent.left
        anchors.leftMargin: 16
        anchors.right: parent.right
        anchors.rightMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        spacing: 2

        Row {
            spacing: 6
            width: parent.width
            Text {
                text: card.taskData.title || ""
                color: Theme.text
                font.family: Theme.font
                font.pixelSize: 12
                font.weight: Font.DemiBold
                elide: Text.ElideRight
                width: parent.width - prioBadge.width - 6
            }
            Rectangle {
                id: prioBadge
                radius: 3
                color: Theme.priorityColor(card.taskData.priority || "normal")
                width: prioText.implicitWidth + 8
                height: prioText.implicitHeight + 2
                anchors.verticalCenter: parent.verticalCenter
                Text {
                    id: prioText
                    anchors.centerIn: parent
                    text: (card.taskData.priority || "").toUpperCase()
                    color: Theme.crust
                    font.family: Theme.mono
                    font.pixelSize: 8
                    font.weight: Font.Bold
                }
            }
        }
        Row {
            spacing: 8
            Text {
                text: AppState.fmtCountdown(card.taskData.due_in_minutes || 0)
                color: Theme.subtext
                font.family: Theme.mono
                font.pixelSize: 10
            }
            Text {
                text: "· " + (card.taskData.estimated_minutes || 0) + "m"
                color: Theme.overlay0
                font.family: Theme.mono
                font.pixelSize: 10
            }
            Text {
                visible: !!card.taskData.course
                text: "· " + (card.taskData.course || "")
                color: card.taskData.color || Theme.overlay0
                font.family: Theme.mono
                font.pixelSize: 10
                font.weight: Font.DemiBold
            }
        }
    }

    MouseArea {
        id: ma
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: toggleProc.running = true
    }

    Process {
        id: toggleProc
        // Stub: would call `orbital mark-in-progress <id>` once that subcommand exists.
        command: ["notify-send", "Orbital", "Clicked: " + (card.taskData.title || "")]
    }
}
