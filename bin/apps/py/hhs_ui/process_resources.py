"""Process-wide Streamlit resource registries."""

from __future__ import annotations

import logging
import sys

from . import constants as hhs_ui_constants


def process_resource_state() -> dict[str, object]:
    """Return process-wide resources that must survive Streamlit reruns."""
    state = getattr(sys, hhs_ui_constants.PROCESS_RESOURCE_STATE_KEY, None)
    if not isinstance(state, dict):
        state = {}
        setattr(sys, hhs_ui_constants.PROCESS_RESOURCE_STATE_KEY, state)
    return state


def process_resource_registry(key: str) -> dict:
    """Return a process-wide mutable registry by key."""
    state = process_resource_state()
    registry = state.get(key)
    if not isinstance(registry, dict):
        registry = {}
        state[key] = registry
    return registry


class FooterStatusLogHandler(logging.Handler):
    """Capture logged warnings and errors for the footer status bar."""

    def emit(self, record: logging.LogRecord) -> None:
        """Append one formatted warning or error record to process storage."""
        if record.levelno < logging.WARNING:
            return
        try:
            message = self.format(record).strip()
            if not message:
                return
            registry = process_resource_registry(
                hhs_ui_constants.FOOTER_STATUS_LOG_RECORDS_REGISTRY_KEY
            )
            records = registry.setdefault("records", [])
            if not isinstance(records, list):
                records = []
                registry["records"] = records
            records.append(
                {
                    "level": record.levelname,
                    "logger": record.name,
                    "message": message,
                }
            )
            del records[: -hhs_ui_constants.FLOATING_STATUS_QUEUE_LIMIT]
        except Exception:
            return


def install_footer_status_log_handler() -> None:
    """Install one footer status log handler on runtime warning/error loggers."""
    registry = process_resource_registry(
        hhs_ui_constants.FOOTER_STATUS_LOG_HANDLER_REGISTRY_KEY
    )
    handler = registry.get("handler")
    if not isinstance(handler, FooterStatusLogHandler):
        handler = FooterStatusLogHandler()
        handler.setLevel(logging.WARNING)
        handler.setFormatter(logging.Formatter("%(message)s"))
        registry["handler"] = handler

    logging.captureWarnings(True)
    logger_names = {
        name
        for name, logger in logging.Logger.manager.loggerDict.items()
        if name == "py.warnings"
        or name == "streamlit"
        or (name.startswith("streamlit.") and isinstance(logger, logging.Logger))
    }
    logger_names.update(("", "py.warnings", "streamlit"))
    for logger_name in logger_names:
        logger = logging.getLogger(logger_name)
        if not any(
            isinstance(existing_handler, FooterStatusLogHandler)
            for existing_handler in logger.handlers
        ):
            logger.addHandler(handler)
    registry["installed"] = True
