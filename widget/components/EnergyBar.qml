// Slack indicator: green when you have buffer, red when overbooked.
import QtQuick
import "."

Item {
    id: bar
    implicitHeight: 36

    readonly property int slack: AppState.today.slack_minutes || 0
    readonly property bool over: slack < 0

    Column {
        anchors.fill: parent
        spacing: 4

        Row {
            width: parent.width
            Text {
                text: bar.over ? "Overbooked" : "Today's slack"
                color: Theme.subtext
                font.family: Theme.font
                font.pixelSize: 11
            }
            Item { width: parent.width - leftLabel.width - rightLabel.width; height: 1 }
            Text {
                id: rightLabel
                text: {
                    const m = Math.abs(bar.slack);
                    const h = Math.floor(m / 60);
                    const r = m % 60;
                    return (bar.over ? "-" : "") + h + "h " + r + "m";
                }
                color: bar.over ? Theme.red : Theme.green
                font.family: Theme.mono
                font.pixelSize: 11
                font.weight: Font.DemiBold
            }
            Text { id: leftLabel; visible: false; text: "Today's slack" }   // for width calc parity
        }

        Rectangle {
            width: parent.width
            height: 6
            radius: 3
            color: Theme.surface0
            Rectangle {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                radius: 3
                // capped 0..1 fraction
                width: parent.width * Math.min(1.0, Math.max(0.0, bar.over
                    ? Math.min(1.0, Math.abs(bar.slack) / 240)
                    : bar.slack / (15 * 60)))
                color: bar.over ? Theme.red : Theme.green
                Behavior on width { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }
            }
        }
    }
}
