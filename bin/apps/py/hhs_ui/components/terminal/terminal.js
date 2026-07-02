const STREAMLIT_RENDER_EVENT = "streamlit:render";
const DEFAULT_TERMINAL_HEIGHT = 520;
const MIN_TERMINAL_HEIGHT = 360;
const PARENT_BOTTOM_GUARD_PX = 116;
const terminalShell = document.getElementById("terminal-shell");
const terminalHost = document.getElementById("terminal");

let terminal = null;
let fitAddon = null;
let promptText = "$ ";
let commandBuffer = "";
let commandCursor = 0;
let commandHistory = [];
let historyIndex = 0;
let lastTranscript = null;
let pendingRender = null;
let terminalReady = false;

/**
 * Send a Streamlit component protocol message to the parent frame.
 * @param {string} type Streamlit protocol message type.
 * @param {object} data Message payload.
 */
function sendStreamlitMessage(type, data = {}) {
  window.parent.postMessage(
    {
      isStreamlitMessage: true,
      type,
      ...data,
    },
    "*",
  );
}

/**
 * Tell Streamlit that this component can receive render events.
 */
function setComponentReady() {
  window.addEventListener("message", handleStreamlitMessage);
  sendStreamlitMessage("streamlit:componentReady", { apiVersion: 1 });
}

/**
 * Send the current component height to Streamlit.
 */
function setFrameHeight() {
  const height = Math.ceil(terminalShell.getBoundingClientRect().height);
  sendStreamlitMessage("streamlit:setFrameHeight", {
    height,
  });
}

/**
 * Send a submitted terminal command to Streamlit.
 * @param {string} command Command line entered by the user.
 */
function submitCommand(command) {
  sendStreamlitMessage("streamlit:setComponentValue", {
    dataType: "json",
    value: {
      command,
      eventId: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    },
  });
}

/**
 * Normalize terminal line endings for xterm.js.
 * @param {string} value Text containing terminal output.
 * @returns {string} Output with CRLF line endings.
 */
function normalizeTerminalText(value) {
  return value.replace(/\r?\n/g, "\r\n");
}

/**
 * Fit the terminal viewport and scroll to the latest terminal content.
 */
function scrollTerminalToContent() {
  if (!terminal || !fitAddon) {
    return;
  }
  window.requestAnimationFrame(() => {
    fitAddon.fit();
    terminal.scrollToBottom();
    terminal.focus();
    setFrameHeight();
    window.requestAnimationFrame(() => {
      terminal.scrollToBottom();
      setFrameHeight();
    });
  });
}

/**
 * Return the tallest terminal height that fits in the visible right panel.
 * @param {number} requestedHeight Explicit height provided by Python.
 * @returns {number} Terminal height in pixels.
 */
function terminalHeight(requestedHeight) {
  if (Number.isFinite(requestedHeight) && requestedHeight > 0) {
    return requestedHeight;
  }
  try {
    const frame = window.frameElement;
    if (frame && window.parent) {
      const frameRect = frame.getBoundingClientRect();
      const parentHeight = window.parent.innerHeight || DEFAULT_TERMINAL_HEIGHT;
      const availableHeight = parentHeight - frameRect.top - PARENT_BOTTOM_GUARD_PX;
      return Math.max(MIN_TERMINAL_HEIGHT, Math.floor(availableHeight));
    }
  } catch (_error) {
    return DEFAULT_TERMINAL_HEIGHT;
  }
  return DEFAULT_TERMINAL_HEIGHT;
}

/**
 * Apply Streamlit theme values to the terminal frame.
 * @param {object|undefined} theme Streamlit theme object.
 */
function applyTheme(theme) {
  if (!theme) {
    return;
  }
  const terminalBorderColor = String(
    pendingRender?.args?.borderColor || theme.borderColor || theme.primaryColor || "currentColor",
  );
  document.documentElement.style.setProperty(
    "--hhs-terminal-background",
    theme.secondaryBackgroundColor || theme.backgroundColor || "#17161f",
  );
  document.documentElement.style.setProperty(
    "--hhs-terminal-text",
    theme.textColor || "#f8f8f2",
  );
  document.documentElement.style.setProperty(
    "--hhs-terminal-border",
    terminalBorderColor,
  );
  if (terminal) {
    const terminalTheme = {
      background: theme.secondaryBackgroundColor || theme.backgroundColor || "#17161f",
      foreground: theme.textColor || "#f8f8f2",
      cursor: theme.primaryColor || "#ffd866",
    };
    const selectionColor = theme.primaryColor || theme.borderColor;
    if (selectionColor) {
      terminalTheme.selectionBackground = `${selectionColor}55`;
    }
    terminal.options = {
      theme: terminalTheme,
    };
  }
}

/**
 * Clamp the command cursor to the current editable command line.
 * @param {number} nextCursor Requested command cursor offset.
 * @returns {number} Valid command cursor offset.
 */
function clampedCommandCursor(nextCursor) {
  return Math.max(0, Math.min(nextCursor, commandBuffer.length));
}

/**
 * Redraw the editable command line and place the xterm cursor at the command cursor.
 */
function renderCommandLine() {
  commandCursor = clampedCommandCursor(commandCursor);
  terminal.write(`\x1b[2K\r${promptText}${commandBuffer}`);
  const charsToMoveLeft = commandBuffer.length - commandCursor;
  if (charsToMoveLeft > 0) {
    terminal.write(`\x1b[${charsToMoveLeft}D`);
  }
}

/**
 * Replace the editable command line.
 * @param {string} nextCommand Command line to show.
 * @param {number|undefined} nextCursor Cursor offset after replacement.
 */
function replaceCommandLine(nextCommand, nextCursor = nextCommand.length) {
  commandBuffer = nextCommand;
  commandCursor = clampedCommandCursor(nextCursor);
  renderCommandLine();
}

/**
 * Insert printable text at the current command cursor.
 * @param {string} text Text to insert.
 */
function insertCommandText(text) {
  commandBuffer =
    commandBuffer.slice(0, commandCursor) + text + commandBuffer.slice(commandCursor);
  commandCursor += text.length;
  renderCommandLine();
}

/**
 * Delete a range from the current command line and redraw it.
 * @param {number} startIndex First character offset to delete.
 * @param {number} endIndex Character offset after the deleted range.
 */
function deleteCommandRange(startIndex, endIndex) {
  const start = clampedCommandCursor(startIndex);
  const end = clampedCommandCursor(endIndex);
  if (end <= start) {
    return;
  }
  commandBuffer = commandBuffer.slice(0, start) + commandBuffer.slice(end);
  commandCursor = start;
  renderCommandLine();
}

/**
 * Return the cursor offset at the beginning of the previous shell word.
 * @returns {number} Previous word offset.
 */
function previousWordCursor() {
  let index = commandCursor;
  while (index > 0 && /\s/.test(commandBuffer[index - 1])) {
    index -= 1;
  }
  while (index > 0 && !/\s/.test(commandBuffer[index - 1])) {
    index -= 1;
  }
  return index;
}

/**
 * Return the cursor offset after the next shell word.
 * @returns {number} Next word offset.
 */
function nextWordCursor() {
  let index = commandCursor;
  while (index < commandBuffer.length && /\s/.test(commandBuffer[index])) {
    index += 1;
  }
  while (index < commandBuffer.length && !/\s/.test(commandBuffer[index])) {
    index += 1;
  }
  return index;
}

/**
 * Clear the visible terminal buffer while preserving the current editable line.
 */
function clearVisibleTerminal() {
  terminal.clear();
  renderCommandLine();
  scrollTerminalToContent();
}

/**
 * Clear the visible terminal and ask Streamlit to clear the persisted transcript.
 */
function clearPersistedTerminal() {
  terminal.clear();
  commandBuffer = "";
  commandCursor = 0;
  terminal.write(promptText);
  scrollTerminalToContent();
  submitCommand("clear");
}

/**
 * Cancel the current editable line without sending it to Streamlit.
 */
function cancelCommandLine() {
  terminal.write("^C\r\n");
  commandBuffer = "";
  commandCursor = 0;
  terminal.write(promptText);
}

/**
 * Move through terminal command history.
 * @param {number} direction Negative for previous, positive for next.
 */
function moveCommandHistory(direction) {
  if (commandHistory.length === 0) {
    return;
  }
  historyIndex = clampedHistoryIndex(historyIndex + direction);
  replaceCommandLine(commandHistory[historyIndex] || "");
}

/**
 * Clamp the command history index to available history entries.
 * @param {number} nextIndex Requested history index.
 * @returns {number} Valid history index.
 */
function clampedHistoryIndex(nextIndex) {
  return Math.max(0, Math.min(nextIndex, commandHistory.length));
}

/**
 * Emulate a terminal control or navigation shortcut in the UI.
 * @param {string} data Input emitted by xterm.js.
 * @returns {boolean} Whether the input was handled.
 */
function handleTerminalShortcut(data) {
  const shortcuts = {
    "\x1b[A": () => moveCommandHistory(-1),
    "\x10": () => moveCommandHistory(-1),
    "\x1b[B": () => moveCommandHistory(1),
    "\x0e": () => moveCommandHistory(1),
    "\x1b[D": () => replaceCommandLine(commandBuffer, commandCursor - 1),
    "\x02": () => replaceCommandLine(commandBuffer, commandCursor - 1),
    "\x1b[C": () => replaceCommandLine(commandBuffer, commandCursor + 1),
    "\x06": () => replaceCommandLine(commandBuffer, commandCursor + 1),
    "\x1b[H": () => replaceCommandLine(commandBuffer, 0),
    "\x1bOH": () => replaceCommandLine(commandBuffer, 0),
    "\x1b[1~": () => replaceCommandLine(commandBuffer, 0),
    "\x01": () => replaceCommandLine(commandBuffer, 0),
    "\x1b[F": () => replaceCommandLine(commandBuffer, commandBuffer.length),
    "\x1bOF": () => replaceCommandLine(commandBuffer, commandBuffer.length),
    "\x1b[4~": () => replaceCommandLine(commandBuffer, commandBuffer.length),
    "\x05": () => replaceCommandLine(commandBuffer, commandBuffer.length),
    "\x1bb": () => replaceCommandLine(commandBuffer, previousWordCursor()),
    "\x1b[1;5D": () => replaceCommandLine(commandBuffer, previousWordCursor()),
    "\x1bf": () => replaceCommandLine(commandBuffer, nextWordCursor()),
    "\x1b[1;5C": () => replaceCommandLine(commandBuffer, nextWordCursor()),
    "\x1b[3~": () => deleteCommandRange(commandCursor, commandCursor + 1),
    "\x04": () => deleteCommandRange(commandCursor, commandCursor + 1),
    "\u007f": () => deleteCommandRange(commandCursor - 1, commandCursor),
    "\x08": () => deleteCommandRange(commandCursor - 1, commandCursor),
    "\x0b": clearPersistedTerminal,
    "\x15": () => deleteCommandRange(0, commandCursor),
    "\x17": () => deleteCommandRange(previousWordCursor(), commandCursor),
    "\x0c": clearPersistedTerminal,
    "\x03": cancelCommandLine,
    "\x1b[5~": () => terminal.scrollPages(-1),
    "\x1b[6~": () => terminal.scrollPages(1),
    "\x1b": () => {},
  };
  const shortcut = shortcuts[data];
  if (!shortcut) {
    return false;
  }
  shortcut();
  return true;
}

/**
 * Handle browser-level terminal shortcuts that xterm.js does not emit as data.
 * @param {KeyboardEvent} event Keyboard event emitted by the terminal host.
 */
function handleTerminalKeydown(event) {
  if (event.key.toLowerCase() !== "k" || (!event.metaKey && !event.ctrlKey)) {
    return;
  }
  event.preventDefault();
  event.stopPropagation();
  clearPersistedTerminal();
}

/**
 * Handle arrow-key escape sequences and printable terminal input.
 * @param {string} data Input emitted by xterm.js.
 */
function handleTerminalData(data) {
  if (!terminalReady) {
    return;
  }

  if (handleTerminalShortcut(data)) {
    return;
  }

  for (const char of data) {
    if (char === "\r") {
      const command = commandBuffer;
      terminal.write("\r\n");
      if (command.trim()) {
        commandHistory.push(command);
      }
      historyIndex = commandHistory.length;
      commandBuffer = "";
      commandCursor = 0;
      submitCommand(command);
      return;
    }

    if (char >= " " || char === "\t") {
      insertCommandText(char);
    }
  }
}

/**
 * Render a new transcript from Streamlit into xterm.js.
 * @param {object} args Component render arguments.
 */
function renderTerminal(args) {
  const height = terminalHeight(Number(args.height || 0));
  const transcript = String(args.transcript || "");
  promptText = String(args.prompt || "$ ");
  commandHistory = Array.isArray(args.history) ? args.history : commandHistory;
  historyIndex = commandHistory.length;
  terminalShell.style.height = `${height}px`;
  terminalShell.style.minHeight = `${height}px`;

  if (transcript !== lastTranscript) {
    terminal.reset();
    const transcriptText = transcript
      ? `${normalizeTerminalText(transcript)}${transcript.endsWith("\n") ? "" : "\r\n"}`
      : "";
    if (transcriptText) {
      terminal.write(`${transcriptText}${promptText}`, scrollTerminalToContent);
    } else {
      terminal.write(promptText, scrollTerminalToContent);
    }
    commandBuffer = "";
    commandCursor = 0;
    lastTranscript = transcript;
  } else {
    scrollTerminalToContent();
  }

  setFrameHeight();
}

/**
 * Handle Streamlit render messages.
 * @param {MessageEvent} event Browser message event.
 */
function handleStreamlitMessage(event) {
  if (!event.data || event.data.type !== STREAMLIT_RENDER_EVENT) {
    return;
  }
  pendingRender = event.data;
  applyTheme(pendingRender.theme);
  if (terminal) {
    renderTerminal(pendingRender.args || {});
  }
}

/**
 * Replace the terminal area with a loading failure message.
 * @param {unknown} error Module loading error.
 */
function renderFallback(error) {
  terminalHost.className = "terminal-fallback";
  terminalHost.textContent = `Unable to load terminal renderer: ${error}`;
  setFrameHeight();
}

/**
 * Load xterm.js and initialize the terminal surface.
 */
async function initializeTerminal() {
  try {
    const [{ Terminal }, { FitAddon }] = await Promise.all([
      import("https://cdn.jsdelivr.net/npm/@xterm/xterm@5.5.0/+esm"),
      import("https://cdn.jsdelivr.net/npm/@xterm/addon-fit@0.10.0/+esm"),
    ]);
    terminal = new Terminal({
      allowProposedApi: false,
      cursorBlink: true,
      cursorStyle: "underline",
      fontFamily: "Droid Sans Mono for Powerline Nerd Font Complete, monospace",
      fontSize: 14,
      scrollback: 5000,
      theme: {
        background: "#17161f",
        foreground: "#f8f8f2",
        cursor: "#ffd866",
      },
    });
    fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);
    terminal.open(terminalHost);
    terminal.onData(handleTerminalData);
    terminalHost.addEventListener("keydown", handleTerminalKeydown, true);
    window.addEventListener("resize", () => {
      if (pendingRender) {
        renderTerminal(pendingRender.args || {});
      } else {
        scrollTerminalToContent();
      }
    });
    terminalReady = true;
    if (pendingRender) {
      applyTheme(pendingRender.theme);
      renderTerminal(pendingRender.args || {});
    }
    setFrameHeight();
  } catch (error) {
    renderFallback(error);
  }
}

setComponentReady();
initializeTerminal();
