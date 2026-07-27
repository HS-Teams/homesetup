#!/usr/bin/env python3
"""Browser-side DOM helper scripts for the HomeSetup Streamlit UI."""

from __future__ import annotations

from collections.abc import Callable


def _unconfigured_dependency(name: str) -> Callable[..., object]:
    """Return a placeholder callback for dependencies configured by streamlit_ui."""

    def dependency(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"DOM script dependency is not configured: {name}")

    return dependency


render_script_html = _unconfigured_dependency("render_script_html")


def configure_dom_scripts(*, render_script_html: Callable[..., None]) -> None:
    """Configure callbacks required by DOM script helpers."""
    globals().update({"render_script_html": render_script_html})


def render_combobox_vt100_shortcuts_script() -> None:
    """Attach Search submission and readline-style shortcuts to combobox inputs."""
    render_script_html(
        """
        <script>
          (() => {
            const parentWindow = window.parent;
            const doc = parentWindow.document;
            if (parentWindow.__hhsComboboxVt100Cleanup) {
              parentWindow.__hhsComboboxVt100Cleanup();
            }
            const isEditableComboboxInput = (node) => {
              if (!node || typeof node.closest !== "function") {
                return false;
              }
              const tagName = String(node.tagName || "").toLowerCase();
              if (tagName !== "input" && tagName !== "textarea") {
                return false;
              }
              if (node.disabled || node.readOnly) {
                return false;
              }
              return Boolean(
                node.closest('[data-baseweb="select"]') ||
                node.closest('[role="combobox"]') ||
                String(node.getAttribute("role") || "").toLowerCase() === "combobox"
              );
            };
            const setNativeValue = (node, value) => {
              const prototype = Object.getPrototypeOf(node);
              const descriptor = Object.getOwnPropertyDescriptor(prototype, "value");
              if (descriptor && descriptor.set) {
                descriptor.set.call(node, value);
                return;
              }
              node.value = value;
            };
            const dispatchInputEvent = (node, inputType, data = null) => {
              let inputEvent = null;
              try {
                inputEvent = new InputEvent("input", {
                  bubbles: true,
                  inputType,
                  data,
                });
              } catch (error) {
                inputEvent = new Event("input", { bubbles: true });
              }
              node.dispatchEvent(inputEvent);
            };
            const normalizedText = (value) =>
              String(value || "").replace(/\s+/g, " ").trim();
            const isVisibleNode = (node) => {
              if (!node || typeof node.getClientRects !== "function") {
                return false;
              }
              if (node.getClientRects().length === 0) {
                return false;
              }
              const style = parentWindow.getComputedStyle(node);
              return style.display !== "none" && style.visibility !== "hidden";
            };
            const isSearchTermsComboboxInput = (node) =>
              isEditableComboboxInput(node) &&
              Boolean(node.closest(".st-key-search_query"));
            const dispatchMouseEvent = (node, eventName) => {
              node.dispatchEvent(
                new MouseEvent(eventName, {
                  bubbles: true,
                  cancelable: true,
                  view: parentWindow,
                })
              );
            };
            const activateComboboxOption = (option) => {
              for (const eventName of ["mousedown", "mouseup", "click"]) {
                dispatchMouseEvent(option, eventName);
              }
            };
            const searchTermsInput = () =>
              Array.from(
                doc.querySelectorAll(
                  '.st-key-search_query input[role="combobox"], ' +
                  ".st-key-search_query input"
                )
              ).find(isVisibleNode) || null;
            const searchSubmitButton = () =>
              Array.from(
                doc.querySelectorAll(".st-key-search_submit_button button")
              ).find(isVisibleNode) || null;
            const searchTermCommitOption = (node) => {
              if (!isSearchTermsComboboxInput(node)) {
                return null;
              }
              const value = normalizedText(node.value);
              if (!value) {
                return null;
              }
              const lowerValue = value.toLowerCase();
              const optionSelectors = [
                '[role="option"]',
                '[data-baseweb="menu"] li',
                '[data-baseweb="popover"] li',
              ];
              return Array.from(
                doc.querySelectorAll(optionSelectors.join(","))
              ).find((option) => {
                if (!isVisibleNode(option)) {
                  return false;
                }
                const text = normalizedText(option.textContent);
                const lowerText = text.toLowerCase();
                return (
                  lowerText === lowerValue ||
                  (lowerText.startsWith("add:") && lowerText.includes(lowerValue))
                );
              }) || null;
            };
            let pendingSearchSubmit = null;
            let pendingSearchSubmitObserver = null;
            let pendingSearchSubmitTimer = null;
            const clearPendingSearchSubmit = () => {
              if (pendingSearchSubmitObserver) {
                pendingSearchSubmitObserver.disconnect();
                pendingSearchSubmitObserver = null;
              }
              if (pendingSearchSubmitTimer) {
                parentWindow.clearTimeout(pendingSearchSubmitTimer);
                pendingSearchSubmitTimer = null;
              }
              pendingSearchSubmit = null;
            };
            const clickPendingSearchSubmit = (allowOriginalInput = false) => {
              if (!pendingSearchSubmit) {
                return false;
              }
              const currentInput = searchTermsInput();
              if (
                !currentInput ||
                normalizedText(currentInput.value) !== pendingSearchSubmit.value ||
                (!allowOriginalInput && currentInput === pendingSearchSubmit.input)
              ) {
                return false;
              }
              const button = searchSubmitButton();
              if (!button || button.disabled) {
                return false;
              }
              clearPendingSearchSubmit();
              button.click();
              return true;
            };
            const queueSearchSubmitAfterTermCommit = (
              node,
              value,
              expectsCommit
            ) => {
              clearPendingSearchSubmit();
              pendingSearchSubmit = { input: node, value };
              pendingSearchSubmitObserver = new parentWindow.MutationObserver(() => {
                parentWindow.requestAnimationFrame(() => {
                  clickPendingSearchSubmit(false);
                });
              });
              pendingSearchSubmitObserver.observe(doc.body, {
                childList: true,
                subtree: true,
              });
              pendingSearchSubmitTimer = parentWindow.setTimeout(() => {
                if (!clickPendingSearchSubmit(true)) {
                  clearPendingSearchSubmit();
                }
              }, expectsCommit ? 750 : 0);
            };
            const selectionState = (node) => {
              const value = String(node.value || "");
              const fallback = value.length;
              const rawStart = Number.isInteger(node.selectionStart)
                ? node.selectionStart
                : fallback;
              const rawEnd = Number.isInteger(node.selectionEnd)
                ? node.selectionEnd
                : rawStart;
              const start = Math.max(0, Math.min(rawStart, value.length));
              const end = Math.max(start, Math.min(rawEnd, value.length));
              return { value, start, end };
            };
            const setCaret = (
              node,
              position,
              length = String(node.value || "").length
            ) => {
              if (typeof node.setSelectionRange !== "function") {
                return;
              }
              const cursor = Math.max(0, Math.min(position, length));
              node.setSelectionRange(cursor, cursor);
            };
            const replaceRange = (node, start, end, replacement, inputType) => {
              const state = selectionState(node);
              const boundedStart = Math.max(0, Math.min(start, state.value.length));
              const boundedEnd = Math.max(boundedStart, Math.min(end, state.value.length));
              const nextValue =
                state.value.slice(0, boundedStart) +
                replacement +
                state.value.slice(boundedEnd);
              setNativeValue(node, nextValue);
              setCaret(node, boundedStart + replacement.length, nextValue.length);
              dispatchInputEvent(node, inputType, replacement || null);
            };
            const previousWordStart = (value, start) => {
              let index = Math.max(0, Math.min(start, value.length));
              while (index > 0 && /\s/.test(value.charAt(index - 1))) {
                index -= 1;
              }
              while (index > 0 && !/\s/.test(value.charAt(index - 1))) {
                index -= 1;
              }
              return index;
            };
            const onKeydown = (event) => {
              const node = event.target;
              if (
                event.key === "Enter" &&
                !event.ctrlKey &&
                !event.metaKey &&
                !event.altKey &&
                isSearchTermsComboboxInput(node)
              ) {
                const value = normalizedText(node.value);
                if (value) {
                  const option = searchTermCommitOption(node);
                  const expectsCommit =
                    Boolean(option) ||
                    String(node.getAttribute("aria-expanded")) === "true";
                  queueSearchSubmitAfterTermCommit(node, value, expectsCommit);
                  if (option) {
                    activateComboboxOption(option);
                    event.preventDefault();
                    event.stopPropagation();
                    if (typeof event.stopImmediatePropagation === "function") {
                      event.stopImmediatePropagation();
                    }
                  }
                  return;
                }
              }
              if (!(event.ctrlKey || event.metaKey) || event.altKey) {
                return;
              }
              if (!isEditableComboboxInput(node)) {
                return;
              }
              const key = String(event.key || "").toLowerCase();
              const state = selectionState(node);
              const hasSelection = state.start !== state.end;
              let handled = true;
              switch (key) {
                case "a":
                  setCaret(node, 0, state.value.length);
                  break;
                case "e":
                  setCaret(node, state.value.length, state.value.length);
                  break;
                case "b":
                  setCaret(node, Math.max(0, state.start - 1), state.value.length);
                  break;
                case "f":
                  setCaret(
                    node,
                    Math.min(state.value.length, state.end + 1),
                    state.value.length
                  );
                  break;
                case "d":
                  if (hasSelection) {
                    replaceRange(node, state.start, state.end, "", "deleteContentForward");
                  } else if (state.start < state.value.length) {
                    replaceRange(node, state.start, state.start + 1, "", "deleteContentForward");
                  }
                  break;
                case "h":
                  if (hasSelection) {
                    replaceRange(node, state.start, state.end, "", "deleteContentBackward");
                  } else if (state.start > 0) {
                    replaceRange(node, state.start - 1, state.start, "", "deleteContentBackward");
                  }
                  break;
                case "k":
                  if (state.start < state.value.length) {
                    replaceRange(node, state.start, state.value.length, "", "deleteContentForward");
                  }
                  break;
                case "u":
                  if (hasSelection) {
                    replaceRange(node, state.start, state.end, "", "deleteContentBackward");
                  } else if (state.start > 0) {
                    replaceRange(node, 0, state.start, "", "deleteContentBackward");
                  }
                  break;
                case "w":
                  if (hasSelection) {
                    replaceRange(node, state.start, state.end, "", "deleteContentBackward");
                  } else if (state.start > 0) {
                    replaceRange(
                      node,
                      previousWordStart(state.value, state.start),
                      state.start,
                      "",
                      "deleteWordBackward"
                    );
                  }
                  break;
                default:
                  handled = false;
              }
              if (!handled) {
                return;
              }
              event.preventDefault();
              event.stopPropagation();
              if (typeof event.stopImmediatePropagation === "function") {
                event.stopImmediatePropagation();
              }
            };
            const onMouseDown = (event) => {
              const target = event.target;
              const button =
                target && typeof target.closest === "function"
                  ? target.closest(".st-key-search_submit_button button")
                  : null;
              if (!button || button.disabled) {
                return;
              }
              const input = searchTermsInput();
              const value = normalizedText(input?.value);
              const option = searchTermCommitOption(input);
              if (!value || !option) {
                return;
              }
              queueSearchSubmitAfterTermCommit(input, value, true);
              activateComboboxOption(option);
              event.preventDefault();
              event.stopPropagation();
              if (typeof event.stopImmediatePropagation === "function") {
                event.stopImmediatePropagation();
              }
            };
            doc.addEventListener("mousedown", onMouseDown, true);
            doc.addEventListener("keydown", onKeydown, true);
            parentWindow.__hhsComboboxVt100Cleanup = () => {
              clearPendingSearchSubmit();
              doc.removeEventListener("mousedown", onMouseDown, true);
              doc.removeEventListener("keydown", onKeydown, true);
            };
          })();
        </script>
        """,
        height=0,
        width=0,
    )
