from loguru import logger as log
from src.backend.PluginManager.ActionCore import ActionCore

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import GLib


class CIStatusAction(ActionCore):
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
        count = self.plugin_base.cache.get("ci_failure_count", 0)
        if count == 0:
            self.set_background_color([0, 180, 0, 255])
        else:
            self.set_background_color([180, 0, 0, 255])
        self.set_center_label(str(count))

    def __del__(self):
        if self._timer_id is not None:
            try:
                GLib.idle_add(GLib.source_remove, self._timer_id)
            except Exception:
                pass
