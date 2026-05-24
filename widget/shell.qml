// Orbital — Quickshell entry point.
// Run with:  qs -p ~/orbital/widget
// Toggle:    qs ipc call orbital toggle
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import "components"

ShellRoot {
    id: root
    property bool visiblePanel: true

    IpcHandler {
        target: "orbital"
        function toggle(): void { root.visiblePanel = !root.visiblePanel; }
        function show(): void   { root.visiblePanel = true; }
        function hide(): void   { root.visiblePanel = false; }
    }

    PanelWindow {
        id: panel
        visible: root.visiblePanel
        anchors { top: true; right: true; bottom: true }
        implicitWidth: 400
        exclusiveZone: 0
        color: "transparent"
        WlrLayershell.namespace: "orbital"
        WlrLayershell.layer: WlrLayer.Top

        OrbitalPanel {
            anchors.fill: parent
            anchors.margins: 8
            onCloseRequested: root.visiblePanel = false
        }
    }
}
