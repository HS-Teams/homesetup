#!/usr/bin/env bats

#  Script: footer-alerts.bats
# Purpose: HomeSetup Streamlit UI footer alert history tests.
# Created: Jul 15, 2026
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2026, HomeSetup team

repo_dir="${BATS_TEST_DIRNAME}"
while [[ ! -f "${repo_dir}/install.bash" ]]; do
  repo_dir="${repo_dir}/.."
done
export HHS_REPO_DIR="$(cd "${repo_dir}" && pwd)"
export HHS_HOME="${HHS_REPO_DIR}"

load "${HHS_REPO_DIR}/tests/test_helper"
load_bats_libs
load "${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/ui/tests/hhs-ui-test-helpers.bash"

@test "when footer alerts are recorded then only today's warnings and errors should be listed" {
  export HHS_CACHE_DIR="${BATS_TEST_TMPDIR}/cache"

  run python3 - <<'PY'
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path("bin/apps/py").resolve()))

from hhs_ui.core.alert_history import (
    append_footer_alert,
    clear_footer_alerts,
    footer_alert_priority,
    footer_alerts_file,
    today_footer_alerts,
)

now = datetime.now().astimezone()
assert clear_footer_alerts()
assert append_footer_alert("Wrapped\nwarning", "warning", created_at=now)
assert not append_footer_alert("Wrapped warning", "warn", created_at=now)
assert append_footer_alert("Current error", "error", created_at=now)
assert append_footer_alert(
    "Previous warning",
    "warn",
    created_at=now - timedelta(days=1),
)
alerts = today_footer_alerts(now)
assert [(alert["kind"], alert["message"]) for alert in alerts] == [
    ("warn", "Wrapped warning"),
    ("error", "Current error"),
]
assert footer_alert_priority(alerts) == "error"
assert clear_footer_alerts()
assert footer_alerts_file().is_file()
assert footer_alerts_file().read_text(encoding="utf-8") == ""
PY
  assert_success
}

@test "when rendering footer alerts then the native popover should follow footer conventions" {
  run python3 - <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path("bin/apps/py").resolve()))

from hhs_ui.core.alert_history import footer_alert_glyph
from hhs_ui.widgets.footer_ui import footer_alerts_menu_markup
from hhs_ui.widgets.status_ui import floating_status_glyph

footer_source = Path("bin/apps/py/hhs_ui/widgets/footer_ui.py").read_text()
status_source = Path("bin/apps/py/hhs_ui/widgets/status_ui.py").read_text()
terminal_source = Path("bin/apps/py/hhs_ui/widgets/terminal_ui.py").read_text()
constants_source = Path("bin/apps/py/hhs_ui/core/constants.py").read_text()
base_css = Path("bin/apps/py/hhs_ui/static/css/streamlit_ui.css").read_text()

alerts_markup = footer_source.split("def footer_alerts_menu_markup", 1)[1].split(
    "\ndef ", 1
)[0]
separator_index = alerts_markup.index('class="hhs-footer-glyph"></span>')
menu_index = alerts_markup.index('<details class="hhs-footer-alerts-menu')
assert separator_index < menu_index
assert 'hidden_attribute = "" if alerts else " hidden"' in alerts_markup
assert 'FOOTER_VIEW_ALERTS_QUERY_PARAM = "hhs_view_alerts"' in constants_source
assert 'FOOTER_CLEAR_ALERTS_QUERY_PARAM = "hhs_clear_alerts"' in constants_source
assert 'FOOTER_ALERTS_FILE = HHS_CACHE_DIR / "streamlit-alerts.txt"' in constants_source
assert 'append_footer_alert(clean_message, normalized_kind)' in status_source
assert 'return "" if kind == "info" else footer_alert_glyph(kind)' in status_source
assert 'request_path == "/footer-alert"' in terminal_source
assert 'parentWindow.__hhsRecordFooterAlert(cleanMessage, kind)' in footer_source
assert 'updateAlertsControl(cleanMessage, kind, glyphText)' in footer_source
assert 'title="{html.escape(message, quote=True)}"' in footer_source
assert 'itemMessage.textContent = message;' in footer_source
assert 'footer_alert_message_preview' not in footer_source
assert '>View</button>' in footer_source
assert '>Clear</button>' in footer_source
assert 'render_footer_alerts_dialog' not in footer_source
assert "Today's alerts" not in footer_source
assert '.hhs-footer-alerts-control[hidden]' in base_css
assert '.hhs-footer-alerts-panel' in base_css
assert 'width: min(22rem, calc(100vw - 2rem)) !important' in base_css
assert '--hhs-footer-alerts-list-min-height: 80px' in base_css
assert '.hhs-footer-alerts-panel .hhs-footer-alerts-list' in base_css
assert 'min-height: var(--hhs-footer-alerts-list-min-height)' in base_css
assert '.hhs-footer-alerts-panel .hhs-footer-alerts-list::after' in base_css
assert '.hhs-footer-alerts-trigger .hhs-footer-glyph-button' in base_css
item_rule = base_css.split('.hhs-footer-alerts-item {', 1)[1].split('}', 1)[0]
assert 'min-height:' not in item_rule
assert '--hhs-footer-alerts-button-min-height: 2.25rem' in base_css
assert '.hhs-footer-alerts-item:hover' in base_css
assert 'var(--hhs-theme-primary-color) 18%' in base_css
assert 'gap: var(--hhs-element-std-gap)' in base_css
assert '.hhs-footer-alerts-menu--warn .hhs-footer-glyph-button' in base_css
assert '.hhs-footer-alerts-menu--error .hhs-footer-glyph-button' in base_css
assert '.hhs-footer-alerts-item--warn .hhs-footer-alerts-item-glyph' in base_css
assert '.hhs-footer-alerts-item--error .hhs-footer-alerts-item-glyph' in base_css

empty_markup = footer_alerts_menu_markup([])
assert 'class="hhs-footer-alerts-control" hidden' in empty_markup
alerts_markup = footer_alerts_menu_markup(
    [
        {
            "kind": "warn",
            "message": "Warning message longer than twenty characters",
            "timestamp_iso": "2026-07-15T23:00:00.000-03:00",
        },
        {
            "kind": "error",
            "message": "Complete error message",
            "timestamp_iso": "2026-07-15T23:01:00.000-03:00",
        },
    ]
)
assert 'class="hhs-footer-alerts-control" hidden' not in alerts_markup
assert 'hhs-footer-alerts-menu--error' in alerts_markup
assert 'hhs-footer-alerts-item--warn' in alerts_markup
assert 'hhs-footer-alerts-item--error' in alerts_markup
assert 'Warning message longer than twenty characters' in alerts_markup
assert floating_status_glyph("warn") == footer_alert_glyph("warn")
assert floating_status_glyph("error") == footer_alert_glyph("error")
PY
  assert_success
}
