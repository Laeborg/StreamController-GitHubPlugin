import sys
import types
import pytest
from unittest.mock import MagicMock, patch, call

# ---------------------------------------------------------------------------
# Stub out gi / GLib before importing action modules
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

# Stub src.backend.PluginManager.ActionCore
action_core_mod = types.ModuleType("src.backend.PluginManager.ActionCore")


class _ActionCoreStub:
    def __init__(self, *args, **kwargs):
        self.plugin_base = kwargs.get("plugin_base", MagicMock())
        self._bg_color = None
        self._center_label = None

    def set_background_color(self, color):
        self._bg_color = color

    def set_center_label(self, text):
        self._center_label = text


action_core_mod.ActionCore = _ActionCoreStub
sys.modules["src"] = types.ModuleType("src")
sys.modules["src.backend"] = types.ModuleType("src.backend")
sys.modules["src.backend.PluginManager"] = types.ModuleType("src.backend.PluginManager")
sys.modules["src.backend.PluginManager.ActionCore"] = action_core_mod
sys.modules["src.backend.DeckManagement"] = types.ModuleType("src.backend.DeckManagement")
sys.modules["src.backend.DeckManagement.InputIdentifier"] = types.ModuleType(
    "src.backend.DeckManagement.InputIdentifier"
)

import importlib, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from actions.PRReviewCountAction import PRReviewCountAction
from actions.CIStatusAction import CIStatusAction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pr_action(pr_count=0, force_poll=None):
    plugin_base = MagicMock()
    plugin_base.cache = {"pr_review_count": pr_count, "ci_failure_count": 0}
    if force_poll is not None:
        plugin_base.force_poll = force_poll
    action = PRReviewCountAction.__new__(PRReviewCountAction)
    _ActionCoreStub.__init__(action, plugin_base=plugin_base)
    action._timer_id = None
    return action, plugin_base


def _make_ci_action(ci_count=0):
    plugin_base = MagicMock()
    plugin_base.cache = {"pr_review_count": 0, "ci_failure_count": ci_count}
    action = CIStatusAction.__new__(CIStatusAction)
    _ActionCoreStub.__init__(action, plugin_base=plugin_base)
    action._timer_id = None
    return action, plugin_base


# ---------------------------------------------------------------------------
# PRReviewCountAction tests
# ---------------------------------------------------------------------------

class TestPRReviewCountAction:
    def test_yellow_bg_and_count_label_when_count_gt_0(self):
        action, _ = _make_pr_action(pr_count=3)
        action._update_display()
        assert action._bg_color == [180, 180, 0, 255]
        assert action._center_label == "3"

    def test_green_bg_and_zero_label_when_count_is_0(self):
        action, _ = _make_pr_action(pr_count=0)
        action._update_display()
        assert action._bg_color == [0, 180, 0, 255]
        assert action._center_label == "0"

    def test_key_down_calls_force_poll(self):
        force_poll = MagicMock()
        action, plugin_base = _make_pr_action(force_poll=force_poll)
        action.on_key_down()
        force_poll.assert_called_once()


# ---------------------------------------------------------------------------
# CIStatusAction tests
# ---------------------------------------------------------------------------

class TestCIStatusAction:
    def test_red_bg_and_count_label_when_failures_gt_0(self):
        action, _ = _make_ci_action(ci_count=2)
        action._update_display()
        assert action._bg_color == [180, 0, 0, 255]
        assert action._center_label == "2"

    def test_green_bg_when_no_failures(self):
        action, _ = _make_ci_action(ci_count=0)
        action._update_display()
        assert action._bg_color == [0, 180, 0, 255]
        assert action._center_label == "0"
