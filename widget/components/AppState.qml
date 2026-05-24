// Loads and polls data/state.json; exposes parsed payload to the rest of the UI.
pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

QtObject {
    id: root

    property string statePath: Quickshell.env("ORBITAL_STATE") || (Quickshell.env("HOME") + "/orbital/data/state.json")
    property var data: ({})
    property date now: new Date()
    property string error: ""

    readonly property var courses:       data.courses        || ({})
    readonly property var today:         data.today          || ({lectures: [], slack_minutes: 0, date: ""})
    readonly property var nextTasks:     data.next_tasks     || []
    readonly property var nextCritical:  data.next_critical  || null
    readonly property var heatmap:       data.heatmap        || ({weeks: [], start: ""})
    readonly property string termName:   (data.term || {}).name || "Spring 2026"

    // FileView watches state.json; we also reload on a 60s timer as a safety net.
    property FileView fileView: FileView {
        path: root.statePath
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            try {
                root.data = JSON.parse(text());
                root.error = "";
            } catch (e) {
                root.error = "Parse error: " + e;
            }
        }
        onLoadFailed: function(reason) {
            root.error = "Load failed: " + reason + " (" + root.statePath + ")";
        }
    }

    property Timer reloadTimer: Timer {
        interval: 60000; running: true; repeat: true
        onTriggered: root.fileView.reload()
    }

    property Timer clock: Timer {
        interval: 1000; running: true; repeat: true
        onTriggered: root.now = new Date()
    }

    Component.onCompleted: fileView.reload()

    function minutesUntil(iso) {
        if (!iso) return 0;
        return Math.floor((new Date(iso).getTime() - now.getTime()) / 60000);
    }

    function fmtCountdown(minutes) {
        if (minutes < 0) {
            const m = -minutes;
            return "overdue " + Math.floor(m/60) + "h";
        }
        if (minutes < 60)    return "in " + minutes + "m";
        if (minutes < 1440)  return "in " + Math.floor(minutes/60) + "h " + (minutes%60) + "m";
        return "in " + Math.floor(minutes/1440) + "d";
    }
}
