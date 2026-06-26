import sys
import types
import pytest
from unittest.mock import MagicMock, call

# ---------------------------------------------------------------------------
# Stub gi / GLib before importing action modules
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

# Stub src hierarchy
action_core_mod = types.ModuleType("src.backend.PluginManager.ActionCore")


class _ActionCoreStub:
    def __init__(self, *args, **kwargs):
        self.plugin_base = kwargs.get("plugin_base", MagicMock())

    def set_media(self, **kwargs):
        pass


action_core_mod.ActionCore = _ActionCoreStub
sys.modules.setdefault("src", types.ModuleType("src"))
sys.modules.setdefault("src.backend", types.ModuleType("src.backend"))
sys.modules.setdefault("src.backend.PluginManager", types.ModuleType("src.backend.PluginManager"))
sys.modules["src.backend.PluginManager.ActionCore"] = action_core_mod
sys.modules.setdefault("src.backend.DeckManagement", types.ModuleType("src.backend.DeckManagement"))
sys.modules.setdefault(
    "src.backend.DeckManagement.InputIdentifier",
    types.ModuleType("src.backend.DeckManagement.InputIdentifier"),
)

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from actions.ScreenSummaryAction import render_summary, ScreenSummaryAction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_screen_action(pr_count=0, ci_count=0):
    plugin_base = MagicMock()
    plugin_base.cache = {"pr_review_count": pr_count, "ci_failure_count": ci_count}
    action = ScreenSummaryAction.__new__(ScreenSummaryAction)
    _ActionCoreStub.__init__(action, plugin_base=plugin_base)
    action._timer_id = None
    return action, plugin_base


# ---------------------------------------------------------------------------
# render_summary tests
# ---------------------------------------------------------------------------

class TestRenderSummary:
    def test_returns_pil_image_correct_size(self):
        from PIL import Image
        img = render_summary(0, 0)
        assert isinstance(img, Image.Image)
        assert img.size == (248, 58)

    def test_pr_text_drawn_when_count_gt_0(self):
        img = render_summary(3, 0)
        # Check a region around the PR text position (8, 18) for non-black pixels
        region = img.crop((8, 10, 100, 50))
        pixels = [region.getpixel((x, y)) for y in range(region.height) for x in range(region.width)]
        assert any(p != (0, 0, 0) for p in pixels), (
            "Expected non-black pixels in PR text region for pr_count=3"
        )

    def test_ci_text_drawn_when_count_gt_0(self):
        img = render_summary(0, 2)
        # Check a region around the CI text position (130, 18) for non-black pixels
        region = img.crop((130, 10, 240, 50))
        pixels = [region.getpixel((x, y)) for y in range(region.height) for x in range(region.width)]
        assert any(p != (0, 0, 0) for p in pixels), (
            "Expected non-black pixels in CI text region for ci_count=2"
        )

    def test_pr_color_yellow_when_count_gt_0(self):
        img = render_summary(1, 0)
        region = img.crop((8, 10, 100, 50))
        pixels = [region.getpixel((x, y)) for y in range(region.height) for x in range(region.width)]
        # Yellow is (255, 220, 0) - check that at least one pixel has high R and G but low B
        assert any(p[0] > 200 and p[1] > 150 and p[2] < 50 for p in pixels), (
            "Expected yellow pixels in PR text region"
        )

    def test_ci_color_red_when_count_gt_0(self):
        img = render_summary(0, 1)
        region = img.crop((130, 10, 240, 50))
        pixels = [region.getpixel((x, y)) for y in range(region.height) for x in range(region.width)]
        # Red is (255, 80, 80) - check high R, low G and B
        assert any(p[0] > 200 and p[1] < 150 and p[2] < 150 for p in pixels), (
            "Expected red pixels in CI text region"
        )


# ---------------------------------------------------------------------------
# ScreenSummaryAction._update_screen tests
# ---------------------------------------------------------------------------

class TestScreenSummaryAction:
    def test_update_screen_calls_set_media_with_image(self):
        from PIL import Image
        action, _ = _make_screen_action(pr_count=2, ci_count=1)
        action.set_media = MagicMock()
        action._update_screen()
        action.set_media.assert_called_once()
        _, kwargs = action.set_media.call_args
        assert "image" in kwargs
        assert isinstance(kwargs["image"], Image.Image)
