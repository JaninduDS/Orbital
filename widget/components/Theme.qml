// Catppuccin Mocha palette + spacing constants.
pragma Singleton
import QtQuick

QtObject {
    readonly property color base:      "#1e1e2e"
    readonly property color mantle:    "#181825"
    readonly property color crust:     "#11111b"
    readonly property color surface0:  "#313244"
    readonly property color surface1:  "#45475a"
    readonly property color overlay0:  "#6c7086"
    readonly property color text:      "#cdd6f4"
    readonly property color subtext:   "#a6adc8"
    readonly property color red:       "#f38ba8"
    readonly property color amber:     "#fab387"
    readonly property color yellow:    "#f9e2af"
    readonly property color green:     "#a6e3a1"
    readonly property color teal:      "#94e2d5"
    readonly property color blue:      "#89b4fa"
    readonly property color mauve:     "#cba6f7"

    readonly property int  pad:        12
    readonly property int  gap:        8
    readonly property int  radius:     10
    readonly property string font:     "Inter"
    readonly property string mono:     "JetBrainsMono Nerd Font"

    function priorityColor(p) {
        switch (p) {
            case "critical": return red;
            case "high":     return amber;
            case "normal":   return teal;
            case "low":      return overlay0;
        }
        return overlay0;
    }
}
