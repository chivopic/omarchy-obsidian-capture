import QtQuick
import QtQuick.Controls
import Quickshell.Io
import qs.Commons
import qs.Commons as Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "io.github.chivopic.obsidian-capture"
  property bool popupOpen: false
  property string draft: ""
  property string status: ""
  property string savedText: ""
  readonly property bool opened: popupOpen
  readonly property string writerPath: decodeURIComponent(String(Qt.resolvedUrl("scripts/obsidian-capture")).replace(/^file:\/\//, ""))
  readonly property string destination: String(setting("folder", "Inbox")) || "."

  // Omarchy's shell-level `summon` routes to these methods for bar widgets.
  // Keep this API on the widget root so it works across shell versions without
  // registering one IpcHandler per bar instance/screen.
  function open() { clearStatus.stop(); popupOpen = true; status = "" }
  function close() { popupOpen = false }
  function toggle() { popupOpen ? close() : open() }
  function save() {
    if (!draft.trim() || writer.running) return
    savedText = draft
    clearStatus.stop()
    status = "正在保存…"
    writer.running = true
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: "✎"
    tooltipText: "记录一个想法到 Obsidian"
    horizontalMargin: 9
    fontSize: Style.font.body
    onPressed: function(mouseButton) { if (mouseButton === Qt.LeftButton) root.toggle() }
  }

  Process {
    id: writer
    command: ["python3", root.writerPath, "--stdin-json",
      "--vault", String(root.setting("vaultPath", "")),
      "--folder", String(root.setting("folder", "Inbox")), "--json"]
    stdinEnabled: true
    onStarted: write(JSON.stringify(root.savedText) + "\n")
    stdout: SplitParser { onRead: data => {
      try {
        const result = JSON.parse(data)
        root.status = result.ok ? "已保存：" + String(result.path || "").split("/").pop() : "保存失败：" + (result.error || "请检查配置")
        if (result.ok) {
          // The editor may have changed while the process was writing. Clear
          // only the submitted snapshot so newer text is never discarded.
          if (root.draft === root.savedText) editor.text = ""
          clearStatus.restart()
        }
      } catch (error) { root.status = "保存失败：无法读取结果" }
    } }
    stderr: SplitParser { onRead: data => console.warn("Obsidian Capture:", data) }
    onExited: function(code, exitStatus) {
      if (root.status === "正在保存…") {
        root.status = (code !== 0 || exitStatus !== 0)
          ? "保存失败，请检查配置"
          : "保存失败：未收到保存结果"
      }
    }
  }

  Timer { id: clearStatus; interval: 2200; onTriggered: root.status = "" }

  KeyboardPanel {
    id: panel
    anchorItem: button
    bar: root.bar
    owner: root
    open: root.popupOpen
    focusTarget: editor
    contentWidth: fittedContentWidth(Style.space(390))
    contentHeight: fittedContentHeight(content.implicitHeight)

    Column {
      id: content
      width: parent.width
      spacing: Style.space(12)
      focus: true
      Keys.onEscapePressed: root.close()

      Item {
        width: parent.width
        height: Math.max(heading.implicitHeight, destinationLabel.implicitHeight)
        Text {
          id: heading
          text: "捕捉想法"
          color: Commons.Color.foreground
          font.family: Style.font.family
          font.pixelSize: Style.font.subtitle
        }
        Text {
          id: destinationLabel
          anchors.right: parent.right
          width: Math.max(0, parent.width - heading.width - Style.space(12))
          text: "Obsidian · " + root.destination
          horizontalAlignment: Text.AlignRight
          elide: Text.ElideLeft
          color: Commons.Color.muted
          font.family: Style.font.family
          font.pixelSize: Style.font.caption
        }
      }

      Rectangle {
        width: parent.width
        height: Style.space(190)
        radius: Style.space(8)
        color: Qt.rgba(Commons.Color.foreground.r, Commons.Color.foreground.g, Commons.Color.foreground.b, 0.05)
        border.color: Commons.Color.popups.border
        TextArea {
          id: editor
          anchors.fill: parent
          anchors.margins: Style.space(10)
          focus: true
          text: root.draft
          placeholderText: "想到什么就写下来…\n首行会用作笔记标题。"
          color: Commons.Color.foreground
          selectedTextColor: Commons.Color.foreground
          selectionColor: Commons.Color.accent
          font.family: Style.font.family
          font.pixelSize: Style.font.body
          wrapMode: TextEdit.Wrap
          background: null
          onTextChanged: root.draft = text
          Keys.onEscapePressed: root.close()
          Keys.onShortcutOverride: event => { if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_Return) event.accepted = true }
          Keys.onPressed: event => {
            if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_Return) {
              event.accepted = true
              root.save()
            }
          }
        }
      }

      Row {
        width: parent.width
        spacing: Style.space(8)
        Text {
          width: parent.width - saveButton.width - parent.spacing
          height: saveButton.height
          text: root.status || "Ctrl + Enter 保存 · Esc 关闭"
          color: root.status.indexOf("失败") !== -1 ? Commons.Color.urgent : Commons.Color.muted
          font.family: Style.font.family
          font.pixelSize: Style.font.caption
          verticalAlignment: Text.AlignVCenter
          elide: Text.ElideRight
        }
        Button {
          id: saveButton
          text: writer.running ? "保存中…" : "保存笔记"
          enabled: root.draft.trim().length > 0 && !writer.running
          focusable: true
          onClicked: root.save()
        }
      }
    }
  }
}
