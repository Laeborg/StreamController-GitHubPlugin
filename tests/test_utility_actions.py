import sys
import types
import os
import pytest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Stub out gi / GLib before importing action modules.
# These may already be stubbed by test_actions.py in the same pytest session;
# we overwrite them so our ActionCoreStub variant (with get_settings) is used.
# ---------------------------------------------------------------------------

gi_mock = types.ModuleType("gi")
gi_mock.require_version = MagicMock()
sys.modules["gi"] = gi_mock

gi_repo = types.ModuleType("gi.repository")
glib_mock = MagicMock()
gi_repo.GLib = glib_mock
sys.modules["gi.repository"] = gi_repo

# Stub loguru
loguru_mock = types.ModuleType("loguru")
loguru_mock.logger = MagicMock()
sys.modules["loguru"] = loguru_mock


# ---------------------------------------------------------------------------
# ActionCore stub with get_settings() support
# ---------------------------------------------------------------------------

class _ActionCoreStub:
    def __init__(self, *args, **kwargs):
        self.plugin_base = kwargs.get("plugin_base", MagicMock())
        self._bg_color = None
        self._center_label = None
        self._settings = {}
        self.input_ident = MagicMock()
        self.deck_controller = MagicMock()

    def set_background_color(self, color):
        self._bg_color = color

    def set_center_label(self, text, **kwargs):
        self._center_label = text

    def get_settings(self):
        return self._settings


# Install/update stub modules (handles both fresh run and re-run after test_actions.py)
action_core_mod = sys.modules.get("src.backend.PluginManager.ActionCore")
if action_core_mod is None:
    action_core_mod = types.ModuleType("src.backend.PluginManager.ActionCore")
action_core_mod.ActionCore = _ActionCoreStub

src_mod = sys.modules.get("src") or types.ModuleType("src")
src_backend = sys.modules.get("src.backend") or types.ModuleType("src.backend")
src_pm = sys.modules.get("src.backend.PluginManager") or types.ModuleType("src.backend.PluginManager")
src_dm = sys.modules.get("src.backend.DeckManagement") or types.ModuleType("src.backend.DeckManagement")
src_dm_input = sys.modules.get("src.backend.DeckManagement.InputIdentifier") or types.ModuleType(
    "src.backend.DeckManagement.InputIdentifier"
)

sys.modules.setdefault("src", src_mod)
sys.modules.setdefault("src.backend", src_backend)
sys.modules.setdefault("src.backend.PluginManager", src_pm)
sys.modules["src.backend.PluginManager.ActionCore"] = action_core_mod
sys.modules.setdefault("src.backend.DeckManagement", src_dm)
sys.modules.setdefault("src.backend.DeckManagement.InputIdentifier", src_dm_input)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Force re-import so the updated ActionCore stub is picked up
for mod_name in ["actions.OpenGitHubAction", "actions.GHCommandAction", "actions.TouchKeyStatusAction"]:
    sys.modules.pop(mod_name, None)

from actions.OpenGitHubAction import OpenGitHubAction
from actions.GHCommandAction import GHCommandAction
from actions.TouchKeyStatusAction import TouchKeyStatusAction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_open_github_action(settings=None):
    action = OpenGitHubAction.__new__(OpenGitHubAction)
    _ActionCoreStub.__init__(action)
    if settings:
        action._settings = settings
    return action


def _make_gh_command_action(settings=None):
    action = GHCommandAction.__new__(GHCommandAction)
    _ActionCoreStub.__init__(action)
    action._settings = settings or {"command": "gh pr list"}
    return action


def _make_touch_key_action(ci_count=0, pr_count=0):
    plugin_base = MagicMock()
    plugin_base.cache = {"pr_review_count": pr_count, "ci_failure_count": ci_count}
    action = TouchKeyStatusAction.__new__(TouchKeyStatusAction)
    _ActionCoreStub.__init__(action, plugin_base=plugin_base)
    action._timer_id = None
    action.plugin_base = plugin_base
    action.input_ident = MagicMock()
    action.input_ident.index = 0
    action.deck_controller = MagicMock()
    action.deck_controller.deck.key_count.return_value = 8
    return action


# ---------------------------------------------------------------------------
# OpenGitHubAction tests
# ---------------------------------------------------------------------------

class TestOpenGitHubAction:
    def test_on_key_down_calls_xdg_open_with_default_url(self):
        action = _make_open_github_action()
        with patch("subprocess.run") as mock_run:
            action.on_key_down()
        mock_run.assert_called_once_with(["xdg-open", "https://github.com"], timeout=5)

    def test_on_key_down_uses_custom_url_from_settings(self):
        action = _make_open_github_action(settings={"url": "https://github.com/myorg"})
        with patch("subprocess.run") as mock_run:
            action.on_key_down()
        mock_run.assert_called_once_with(["xdg-open", "https://github.com/myorg"], timeout=5)


# ---------------------------------------------------------------------------
# GHCommandAction tests
# ---------------------------------------------------------------------------

class TestGHCommandAction:
    def test_on_key_down_calls_subprocess_run_with_command_split(self):
        action = _make_gh_command_action(settings={"command": "gh pr list"})
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            action.on_key_down()
        mock_run.assert_called_once_with(["gh", "pr", "list"], capture_output=True, timeout=15)

    def test_on_key_down_sets_ok_label_on_success(self):
        action = _make_gh_command_action()
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            action.on_key_down()
        assert action._center_label == "OK"

    def test_on_key_down_sets_err_label_on_failure(self):
        action = _make_gh_command_action()
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("subprocess.run", return_value=mock_result):
            action.on_key_down()
        assert action._center_label == "ERR"


# ---------------------------------------------------------------------------
# TouchKeyStatusAction tests
# ---------------------------------------------------------------------------

class TestTouchKeyStatusAction:
    def test_update_led_red_when_ci_failures(self):
        action = _make_touch_key_action(ci_count=2, pr_count=0)
        action._update_led()
        deck = action.deck_controller.deck
        expected_hw_index = action.input_ident.index + deck.key_count()
        deck.set_key_color.assert_called_with(expected_hw_index, 180, 0, 0)

    def test_update_led_yellow_when_pr_pending_and_no_ci_failure(self):
        action = _make_touch_key_action(ci_count=0, pr_count=3)
        action._update_led()
        deck = action.deck_controller.deck
        expected_hw_index = action.input_ident.index + deck.key_count()
        deck.set_key_color.assert_called_with(expected_hw_index, 180, 180, 0)

    def test_update_led_green_when_all_clear(self):
        action = _make_touch_key_action(ci_count=0, pr_count=0)
        action._update_led()
        deck = action.deck_controller.deck
        expected_hw_index = action.input_ident.index + deck.key_count()
        deck.set_key_color.assert_called_with(expected_hw_index, 0, 180, 0)
