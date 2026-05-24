// Pulsing ribbon counting down to the next critical deadline.
import QtQuick
import "."

Rectangle {
    id: ribbon
    implicitHeight: 44
    radius: Theme.radius

    readonly property var crit: AppState.nextCritical
    readonly property int mins: crit ? AppState.minutesUntil(crit.due) : -1

    color: {
        if (!crit) return Theme.surface0;
        if (mins < 48 * 60)  return Qt.darker(Theme.red, 1.3);
        if (mins < 7 * 1440) return Qt.darker(Theme.amber, 1.2);
        return Qt.darker(Theme.blue, 1.4);
    }
    border.color: {
        if (!crit) return Theme.surface1;
        if (mins < 48 * 60)  return Theme.red;
        if (mins < 7 * 1440) return Theme.amber;
        return Theme.blue;
    }
    border.width: 1

    Row {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        Rectangle {
            width: 8; height: 8; radius: 4
            anchors.verticalCenter: parent.verticalCenter
            color: ribbon.border.color
            SequentialAnimation on opacity {
                running: ribbon.crit && ribbon.mins < 48 * 60
                loops: Animation.Infinite
                NumberAnimation { to: 0.3; duration: 700 }
                NumberAnimation { to: 1.0; duration: 700 }
            }
        }
        Column {
            anchors.verticalCenter: parent.verticalCenter
            spacing: 1
            Text {
                text: ribbon.crit ? ribbon.crit.title : "All clear"
                color: Theme.text
                font.family: Theme.font
                font.pixelSize: 13
                font.weight: Font.DemiBold
                elide: Text.ElideRight
                width: ribbon.width - 40
            }
            Text {
                visible: ribbon.crit
                text: AppState.fmtCountdown(ribbon.mins)
                color: Theme.subtext
                font.family: Theme.mono
                font.pixelSize: 11
            }
        }
    }
}
