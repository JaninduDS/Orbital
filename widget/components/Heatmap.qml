// 8-week × 7-day heatmap. Opacity = workload minutes, border = max priority.
import QtQuick
import QtQuick.Controls
import "."

Item {
    id: heat

    readonly property var weeks: AppState.heatmap.weeks || []
    readonly property int labelCol: 14
    readonly property int gap: 3
    // Fit 8 columns into available width; cap cell size so it doesn't grow huge.
    readonly property int cellSize: Math.min(
        28,
        Math.floor((width - labelCol - 4 - 7 * gap) / 8)
    )
    readonly property string todayISO: AppState.now.toISOString().slice(0, 10)

    // Drive the parent layout so it reserves enough height for 7 rows + gaps.
    implicitHeight: 7 * cellSize + 6 * gap
    clip: true

    function opacityFor(minutes) {
        if (!minutes) return 0.12;
        return Math.min(1.0, 0.18 + minutes / 480 * 0.82);
    }

    Row {
        anchors.left: parent.left
        anchors.top: parent.top
        spacing: 4

        Column {
            spacing: heat.gap
            Repeater {
                model: ["M", "T", "W", "T", "F", "S", "S"]
                Text {
                    text: modelData
                    width: heat.labelCol
                    height: heat.cellSize
                    color: Theme.overlay0
                    font.family: Theme.mono
                    font.pixelSize: 9
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }

        Repeater {
            model: heat.weeks
            Column {
                spacing: heat.gap
                Repeater {
                    model: modelData
                    Rectangle {
                        width: heat.cellSize
                        height: heat.cellSize
                        radius: 3
                        color: Qt.rgba(0.55, 0.78, 0.97, heat.opacityFor(modelData.minutes))
                        border.color: modelData.max_priority
                            ? Theme.priorityColor(modelData.max_priority)
                            : "transparent"
                        border.width: modelData.max_priority ? 2 : 0

                        SequentialAnimation on opacity {
                            running: modelData.date === heat.todayISO
                            loops: Animation.Infinite
                            NumberAnimation { from: 1.0; to: 0.6; duration: 1100 }
                            NumberAnimation { from: 0.6; to: 1.0; duration: 1100 }
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
