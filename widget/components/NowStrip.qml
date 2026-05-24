// Horizontal timeline 08:00 → 23:00 of today's lectures, with a live "now" line.
import QtQuick
import "."

Item {
    id: strip
    readonly property int dayStartMin: 8 * 60
    readonly property int dayEndMin:   23 * 60
    readonly property int dayMins:     dayEndMin - dayStartMin

    function minOfDay(d) { return d.getHours() * 60 + d.getMinutes(); }
    function xFor(min) {
        const t = (min - dayStartMin) / dayMins;
        return Math.max(0, Math.min(1, t)) * track.width;
    }

    Rectangle {
        id: track
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        height: 44
        radius: 6
        color: Theme.surface0

        // Hour ticks
        Repeater {
            model: strip.dayEndMin / 60 - strip.dayStartMin / 60 + 1
            Rectangle {
                width: 1
                height: parent.height
                color: Theme.surface1
                opacity: 0.4
                x: strip.xFor((strip.dayStartMin / 60 + index) * 60)
            }
        }

        // Lecture blocks
        Repeater {
            model: AppState.today.lectures || []
            Rectangle {
                readonly property int startMin: strip.minOfDay(new Date(modelData.start))
                readonly property int endMin:   strip.minOfDay(new Date(modelData.end))
                x: strip.xFor(startMin)
                width: Math.max(8, strip.xFor(endMin) - strip.xFor(startMin))
                y: 4
                height: track.height - 8
                radius: 4
                color: modelData.color
                opacity: ongoing ? 1.0 : 0.7
                readonly property bool ongoing: {
                    const n = strip.minOfDay(AppState.now);
                    return n >= startMin && n <= endMin;
                }
                border.color: ongoing ? Theme.text : "transparent"
                border.width: ongoing ? 1 : 0

                Text {
                    anchors.centerIn: parent
                    text: modelData.course + " · " + modelData.location
                    color: "#11111b"
                    font.family: Theme.mono
                    font.pixelSize: 9
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                    width: parent.width - 6
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }

        // Now indicator
        Rectangle {
            width: 2
            height: parent.height + 8
            y: -4
            color: Theme.mauve
            x: strip.xFor(strip.minOfDay(AppState.now))
            visible: {
                const n = strip.minOfDay(AppState.now);
                return n >= strip.dayStartMin && n <= strip.dayEndMin;
            }
            Rectangle {
                width: 6; height: 6; radius: 3
                color: Theme.mauve
                anchors.horizontalCenter: parent.horizontalCenter
                y: -3
            }
        }
    }

    // Hour labels under the track
    Row {
        anchors.top: track.bottom
        anchors.left: track.left
        anchors.right: track.right
        anchors.topMargin: 2
        Repeater {
            model: [8, 12, 16, 20, 23]
            Text {
                width: track.width / 5
                text: modelData + ":00"
                color: Theme.overlay0
                font.family: Theme.mono
                font.pixelSize: 9
                horizontalAlignment: Text.AlignLeft
            }
        }
    }

    Text {
        anchors.centerIn: track
        visible: (AppState.today.lectures || []).length === 0
        text: "no lectures today"
        color: Theme.subtext
        font.family: Theme.font
        font.italic: true
        font.pixelSize: 11
    }
}
