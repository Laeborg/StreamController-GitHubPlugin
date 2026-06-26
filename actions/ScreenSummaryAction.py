import os

from loguru import logger as log
from PIL import Image, ImageDraw, ImageFont

from src.backend.PluginManager.ActionCore import ActionCore

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import GLib

SCREEN_W, SCREEN_H = 248, 58
FONT_SIZE = 18

FONT_CANDIDATES = [
    "/usr/share/fonts/google-noto-vf/NotoSansMono[wght].ttf",
    "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
    "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
]


def _load_font(size: int) -> ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_summary(pr_count: int, ci_count: int) -> Image.Image:
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _load_font(FONT_SIZE)

    pr_text = f"PRs: {pr_count}"
    ci_text = f"CI fails: {ci_count}"

    pr_color = (255, 220, 0) if pr_count > 0 else (255, 255, 255)
    ci_color = (255, 80, 80) if ci_count > 0 else (255, 255, 255)

    draw.text((8, 18), pr_text, font=font, fill=pr_color)
    draw.text((130, 18), ci_text, font=font, fill=ci_color)

    return img


class ScreenSummaryAction(ActionCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._timer_id = None

    def on_ready(self):
        self._update_screen()
        self._timer_id = GLib.timeout_add_seconds(30, self._on_timer)

    def _on_timer(self):
        self._update_screen()
        return True

    def _update_screen(self):
        try:
            pr_count = self.plugin_base.cache.get("pr_review_count", 0)
            ci_count = self.plugin_base.cache.get("ci_failure_count", 0)
            img = render_summary(pr_count, ci_count)
            self.set_media(image=img)
        except Exception as e:
            log.error(f"ScreenSummaryAction._update_screen: {e}")

    def get_supported_inputs(self):
        from src.backend.PluginManager.ActionInputSupport import ActionInputSupport
        from src.backend.DeckManagement.InputIdentifier import Input
        return {
            Input.Key: ActionInputSupport.UNSUPPORTED,
            Input.Dial: ActionInputSupport.UNSUPPORTED,
            Input.Touchscreen: ActionInputSupport.UNSUPPORTED,
            Input.TouchKey: ActionInputSupport.UNSUPPORTED,
            Input.Screen: ActionInputSupport.SUPPORTED,
        }

    def __del__(self):
        if self._timer_id is not None:
            try:
                GLib.idle_add(GLib.source_remove, self._timer_id)
            except Exception:
                pass
