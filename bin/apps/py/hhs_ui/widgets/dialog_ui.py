#!/usr/bin/env python3
"""Reusable Streamlit dialog helpers for HomeSetup."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st


def _unconfigured_dependency(name: str) -> Callable[..., object]:
    """Return a placeholder callback for dependencies configured by streamlit_ui."""

    def dependency(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"dialog UI dependency is not configured: {name}")

    return dependency


render_script_html = _unconfigured_dependency("render_script_html")
dismiss_streamlit_dialog = _unconfigured_dependency("dismiss_streamlit_dialog")


def configure_dialog_runtime(
    *,
    render_script_html: Callable[..., None],
    dismiss_streamlit_dialog: Callable[[], None],
) -> None:
    """Configure callbacks required by reusable dialog helpers."""
    globals().update(
        {
            "render_script_html": render_script_html,
            "dismiss_streamlit_dialog": dismiss_streamlit_dialog,
        }
    )


def close_all_dialogs() -> None:
    """Close every Streamlit dialog or inline confirmation controlled by this UI."""
    st.session_state.pop("_hhs_dialog_pending_callback", None)
    st.session_state.pop("_hhs_dialog_button_dismissal", None)
    st.session_state.pop("_hhs_dialog_dismiss_requested", None)
    st.session_state["ai_clear_chat_pending"] = False
    st.session_state["home_tool_action_execute_pending"] = None
    st.session_state["ssh_explorer_delete_pending"] = None
    st.session_state["ssh_connection_dialog_title"] = ""
    st.session_state["footer_shell_version_dialog_title"] = ""
    st.session_state.pop("home_tool_action_operation", None)
    st.session_state.pop("home_tool_action_name", None)
    st.session_state.pop("home_tool_action_message", None)
    st.session_state.pop("home_tool_action_succeeded", None)
    st.session_state.pop("home_tool_tldr_name", None)
    st.session_state.pop("home_tool_tldr_output", None)
    st.session_state.pop("home_tool_tldr_succeeded", None)


def queue_dialog_callback(callback: Callable[[], None] | None) -> None:
    """Queue a dialog button callback for execution after the dialog is dismissed."""
    if callback:
        st.session_state["_hhs_dialog_pending_callback"] = callback


def execute_pending_dialog_callback() -> None:
    """Run one dialog callback that was queued before the dialog was dismissed."""
    callback = st.session_state.pop("_hhs_dialog_pending_callback", None)
    if callable(callback):
        callback()


def handle_dialog_button_click(
    callback: Callable[[], None] | None = None,
    close_callback: Callable[[], None] | None = None,
) -> None:
    """Dismiss the active dialog and defer the button callback until after dismissal."""
    if close_callback:
        close_callback()
    queue_dialog_callback(callback)
    st.session_state["_hhs_dialog_button_dismissal"] = True
    dismiss_streamlit_dialog()


def render_pending_streamlit_dialog_dismiss() -> None:
    """Render a queued browser-side dialog dismiss script during normal dialog flow."""
    if not st.session_state.pop("_hhs_dialog_dismiss_requested", False):
        return
    render_script_html("""
        <script>
          const doc = window.parent.document;
          const dialog = doc.querySelector('[data-testid="stDialog"], [role="dialog"]');
          const close_button = dialog?.querySelector('button[aria-label="Close"]');
          if (close_button) {
            close_button.click();
          } else {
            doc.dispatchEvent(new KeyboardEvent("keydown", {
              bubbles: true,
              cancelable: true,
              key: "Escape"
            }));
          }
        </script>
        """)


def handle_dialog_dismiss(callback: Callable[[], None] | None = None) -> None:
    """Run native dialog-dismiss cleanup unless dismissal came from a dialog button."""
    if st.session_state.pop("_hhs_dialog_button_dismissal", False):
        return
    if callback:
        callback()


def dialog_button_help(button: dict[str, object], label: str) -> str:
    """Return a concise tooltip for one dialog action button."""
    configured_help = str(button.get("help", "")).strip()
    if configured_help:
        return configured_help
    if label.casefold() == "close":
        return "Close this dialog"
    if label.casefold() == "cancel":
        return "Cancel the pending action"
    return f"{label} the pending action"


def pop_dialog(
    title: str,
    message: str = "",
    confirm_key: str = "",
    cancel_key: str = "",
    on_confirm: Callable[[], None] | None = None,
    on_cancel: Callable[[], None] | None = None,
    confirm_label: str = "Confirm",
    cancel_label: str = "Cancel",
    buttons: tuple[dict[str, object], ...] | None = None,
    body: Callable[[], None] | None = None,
    close_callback: Callable[[], None] | None = None,
    dismissible: bool = True,
) -> bool:
    """Render a reusable dialog that defers button callbacks until after dismissal."""
    dialog_buttons = buttons
    if dialog_buttons is None:
        dialog_buttons = (
            {
                "label": confirm_label,
                "key": confirm_key,
                "callback": on_confirm,
            },
            {
                "label": cancel_label,
                "key": cancel_key,
                "callback": on_cancel,
            },
        )

    dismiss_callback = close_callback or on_cancel
    on_dismiss = (
        (lambda: handle_dialog_dismiss(dismiss_callback))
        if dismiss_callback
        else "rerun"
    )

    @st.dialog(title, dismissible=dismissible, on_dismiss=on_dismiss)
    def render_dialog() -> None:
        """Render the configured dialog content and deferred-action buttons."""
        render_pending_streamlit_dialog_dismiss()
        if body:
            body()
        elif message:
            st.write(message)
        visible_buttons = [button for button in dialog_buttons if button.get("key")]
        if not visible_buttons:
            return
        columns = st.columns(len(visible_buttons))
        for column, button in zip(columns, visible_buttons):
            label = str(button.get("label", "Close"))
            key = str(button.get("key", ""))
            callback = button.get("callback")
            with column:
                if st.button(
                    label,
                    key=key,
                    help=dialog_button_help(button, label),
                    width="stretch",
                ):
                    handle_dialog_button_click(
                        callback if callable(callback) else None,
                        close_callback=close_callback,
                    )

    render_dialog()
    return True
