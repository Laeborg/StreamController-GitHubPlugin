from loguru import logger as log
from src.backend.PluginManager.ActionCore import ActionCore

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import GLib


class TouchKeyStatusAction(ActionCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._timer_id = None

    def on_ready(self):
        self._update_led()
        self._timer_id = GLib.timeout_add_seconds(30, self._on_timer)

    def _on_timer(self):
        self._update_led()
        return True

    def _update_led(self):
        cache = self.plugin_base.cache
        ci_failures = cache.get("ci_failure_count", 0)
        pr_count = cache.get("pr_review_count", 0)

        if ci_failures > 0:
            r, g, b = 180, 0, 0
        elif pr_count > 0:
            r, g, b = 180, 180, 0
        else:
            r, g, b = 0, 180, 0

        try:
            hw_index = self.input_ident.index + self.deck_controller.deck.key_count()
            self.deck_controller.deck.set_key_color(hw_index, r, g, b)
        except Exception as e:
            log.error(f"TouchKeyStatusAction: failed to set LED: {e}")

    def get_supported_inputs(self):
        from src.backend.PluginManager.ActionInputSupport import ActionInputSupport
        from src.backend.DeckManagement.InputIdentifier import Input
        return {
            Input.Key: ActionInputSupport.UNSUPPORTED,
            Input.Dial: ActionInputSupport.UNSUPPORTED,
            Input.Touchscreen: ActionInputSupport.UNSUPPORTED,
            Input.TouchKey: ActionInputSupport.SUPPORTED,
            Input.Screen: ActionInputSupport.UNSUPPORTED,
        }

    def __del__(self):
        if self._timer_id is not None:
            try:
                GLib.idle_add(GLib.source_remove, self._timer_id)
            except Exception:
                pass
