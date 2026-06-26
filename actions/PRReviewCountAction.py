from src.backend.PluginManager.ActionCore import ActionCore

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import GLib


class PRReviewCountAction(ActionCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._timer_id = None

    def on_ready(self):
        self._update_display()
        self._timer_id = GLib.timeout_add_seconds(30, self._on_timer)

    def _on_timer(self):
        self._update_display()
        return True

    def _update_display(self):
        count = self.plugin_base.cache.get("pr_review_count", 0)
        if count == 0:
            self.set_background_color([0, 180, 0, 255])
        else:
            self.set_background_color([180, 180, 0, 255])
        self.set_center_label(str(count))

    def get_supported_inputs(self):
        from src.backend.PluginManager.ActionInputSupport import ActionInputSupport
        from src.backend.DeckManagement.InputIdentifier import Input
        return {
            Input.Key: ActionInputSupport.SUPPORTED,
            Input.Dial: ActionInputSupport.UNSUPPORTED,
            Input.Touchscreen: ActionInputSupport.UNSUPPORTED,
            Input.TouchKey: ActionInputSupport.UNSUPPORTED,
            Input.Screen: ActionInputSupport.UNSUPPORTED,
        }

    def on_key_down(self):
        self.plugin_base.force_poll()

    def __del__(self):
        if self._timer_id is not None:
            try:
                GLib.idle_add(GLib.source_remove, self._timer_id)
            except Exception:
                pass
