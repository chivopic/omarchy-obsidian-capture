import QtQuick
import Quickshell

ShellRoot {
  id: root
  property int attempts: 0
  property int phase: 0
  QtObject {
    id: fakeBar
    property bool vertical: false
    property int barSize: 28
    property string position: "top"
    property string fontFamily: "sans-serif"
    property color barForeground: "#eeeeee"
    property color foreground: "#eeeeee"
    property color urgent: "#ff5555"
    property bool foregroundAnimationEnabled: false
    property var activePopout: null
    function registerClickTarget(item) {}
    function unregisterClickTarget(item) {}
    function showTooltip(item, text) {}
    function hideTooltip(item) {}
    function requestPopout(item) { activePopout = item }
    function releasePopout(item) { activePopout = null }
  }
  FloatingWindow {
    implicitWidth: 400
    implicitHeight: 100
    visible: false
    Loader {
      id: widget
      source: Quickshell.env("CAPTURE_PROJECT") + "/BarWidget.qml"
      onLoaded: {
        item.bar = fakeBar
        item.settings = { vaultPath: Quickshell.env("CAPTURE_VAULT"), folder: "Inbox" }
        start.start()
      }
    }
  }
  Timer {
    id: start
    interval: 200
    onTriggered: {
      widget.item.draft = "First line\nOriginal body"
      widget.item.save()
      widget.item.draft = "New unsaved thought"
      check.start()
    }
  }
  Timer {
    id: check
    interval: 100
    repeat: true
    onTriggered: {
      root.attempts++
      if (root.phase === 0 && widget.item.status.indexOf("已保存") !== -1) {
        if (widget.item.draft !== "New unsaved thought") {
          console.error("CAPTURE_QML_FAILED: newer draft was lost")
          Qt.quit()
        } else {
          root.phase = 1
          root.attempts = 0
          widget.item.settings = { vaultPath: Quickshell.env("CAPTURE_VAULT") + "/missing", folder: "Inbox" }
          retry.start()
        }
      } else if (root.phase === 1 && widget.item.status.indexOf("保存失败") !== -1) {
        if (widget.item.draft !== "New unsaved thought")
          console.error("CAPTURE_QML_FAILED: failed save lost draft")
        else
          console.log("CAPTURE_QML_PASSED")
        Qt.quit()
      } else if (root.attempts > 60 || (root.phase === 0 && widget.item.status.indexOf("失败") !== -1)) {
        console.error("CAPTURE_QML_FAILED: " + widget.item.status)
        Qt.quit()
      }
    }
  }
  Timer { id: retry; interval: 300; onTriggered: widget.item.save() }
  Timer { interval: 9000; running: true; onTriggered: Qt.quit() }
}
