// 8-week × 7-day heatmap. Opacity = workload minutes, border = max priority.
import QtQuick
import QtQuick.Controls
import "."

Item {
    id: heat
    readonly property var weeks: AppState.heatmap.weeks || []
    readonly property int cellSize: Math.floor((width - 24) / 8)
    readonly property int gap: 3
    readonly property string todayISO: AppState.now.toISOString().slice(0,10)

    function opacityFor(minutes) {
        if (!minutes) return 0.12;
        // soft log scale; 480 min = saturated
        return Math.min(1.0, 0.18 + minutes / 480 * 0.82);
    }

    Row {
        anchors.left: parent.left
        anchors.top: parent.top
        spacing: 4

        // Day-of-week labels
        Column {
            spacing: heat.gap
            Repeater {
                model: ["M","T","W","T","F","S","S"]
                Text {
                    text: modelData
                    width: 14
                    height: heat.cellSize
                    color: Theme.overlay0
                    font.family: Theme.mono
                    font.pixelSize: 9
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }

        // Week columns
        Repeater {
            model: heat.weeks
            Column {
                spacing: heat.gap
                Repeater {
                    model: modelData   // 7 cells
                    Rectangle {
                        width: heat.cellSize
                        height: heat.cellSize
                        radius: 3
                        color: Qt.rgba(0.55, 0.78, 0.97, heat.opacityFor(modelData.minutes))
                        border.color: modelData.max_priority
                            ? Theme.priorityColor(modelData.max_priority)
                            : "transparent"
                        border.width: modelData.max_priority ? 2 : 0
                        opacity: modelData.date === heat.todayISO ? 1.0 : 0.95
                        scale: modelData.date === heat.todayISO ? 1.05 : 1.0
                        Behavior on scale { NumberAnimation { duration: 200 } }

                        // Pulse today's cell
                        SequentialAnimation on opacity {
                            running: modelData.date === heat.todayISO
                            loops: Animation.Infinite
                            NumberAnimation { from: 1.0; to: 0.7; duration: 1100 }
                            NumberAnimation { from: 0.7; to: 1.0; duration: 1100 }
                        }

                        ToolTip.visible: hover.containsMouse
                        ToolTip.text: modelData.date + "  ·  " + modelData.minutes + "m  ·  " + modelData.count + " tasks"
                        ToolTip.delay: 200
                        MouseArea {
                            id: hover
                            anchors.fill: parent
                            hoverEnabled: true
                        }
                    }
                }
            }
        }
    }
}
