// Orbital — Quickshell entry point.
// Run with:  qs -p ~/orbital/widget
import QtQuick
import Quickshell
import Quickshell.Wayland
import "components"

ShellRoot {
    PanelWindow {
        id: panel
        anchors { top: true; right: true; bottom: true }
        implicitWidth: 400
        exclusiveZone: 0          // float over windows; set >0 to reserve space
        color: "transparent"
        WlrLayershell.namespace: "orbital"
        WlrLayershell.layer: WlrLayer.Top

        OrbitalPanel {
            anchors.fill: parent
            anchors.margins: 8
        }
    }
}
