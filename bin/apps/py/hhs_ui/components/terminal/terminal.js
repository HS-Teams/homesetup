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
    pendingRender?.args?.borderColor || theme.borderColor || theme.primaryColor || "#6d5c99",
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
    terminal.options = {
      theme: {
        background: theme.secondaryBackgroundColor || theme.backgroundColor || "#17161f",
        foreground: theme.textColor || "#f8f8f2",
        cursor: theme.primaryColor || "#ffd866",
        selectionBackground: `${theme.primaryColor || "#6d5c99"}55`,
      },
    };
  }
}

/**
 * Replace the editable command line with a history entry.
 * @param {string} nextCommand Command line to show.
 */
function replaceCommandLine(nextCommand) {
  terminal.write(`\x1b[2K\r${promptText}${nextCommand}`);
  commandBuffer = nextCommand;
}

/**
 * Handle arrow-key escape sequences and printable terminal input.
 * @param {string} data Input emitted by xterm.js.
 */
function handleTerminalData(data) {
  if (!terminalReady) {
    return;
  }

  if (data === "\x1b[A") {
    if (commandHistory.length === 0) {
      return;
    }
    historyIndex = Math.max(0, historyIndex - 1);
    replaceCommandLine(commandHistory[historyIndex] || "");
    return;
  }

  if (data === "\x1b[B") {
    if (commandHistory.length === 0) {
      return;
    }
    historyIndex = Math.min(commandHistory.length, historyIndex + 1);
    replaceCommandLine(commandHistory[historyIndex] || "");
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
      submitCommand(command);
      return;
    }

    if (char === "\u007f") {
      if (commandBuffer.length > 0) {
        commandBuffer = commandBuffer.slice(0, -1);
        terminal.write("\b \b");
      }
      continue;
    }

    if (char === "\u0003") {
      terminal.write("^C\r\n");
      commandBuffer = "";
      terminal.write(promptText);
      continue;
    }

    if (char >= " " || char === "\t") {
      commandBuffer += char;
      terminal.write(char);
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
    if (transcript) {
      terminal.write(normalizeTerminalText(transcript));
      if (!transcript.endsWith("\n")) {
        terminal.write("\r\n");
      }
    }
    terminal.write(promptText);
    commandBuffer = "";
    lastTranscript = transcript;
  }

  window.requestAnimationFrame(() => {
    fitAddon.fit();
    terminal.scrollToBottom();
    terminal.focus();
    setFrameHeight();
  });
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
      fontFamily: "Droid Sans Mono for Powerline Nerd Font Complete, monospace",
      fontSize: 14,
      scrollback: 5000,
      theme: {
        background: "#17161f",
        foreground: "#f8f8f2",
        cursor: "#ffd866",
        selectionBackground: "#6d5c9955",
      },
    });
    fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);
    terminal.open(terminalHost);
    terminal.onData(handleTerminalData);
    window.addEventListener("resize", () => {
      if (pendingRender) {
        renderTerminal(pendingRender.args || {});
      } else {
        fitAddon.fit();
        setFrameHeight();
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
