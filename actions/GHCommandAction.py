import subprocess
from src.backend.PluginManager.ActionCore import ActionCore


class GHCommandAction(ActionCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        label = self.get_settings().get("label", "gh")
        self.set_center_label(label)
        self.set_background_color([20, 20, 20, 255])

    def on_key_down(self):
        settings = self.get_settings()
        command = settings.get("command", "gh pr list")
        result = subprocess.run(command.split(), capture_output=True)
        if result.returncode == 0:
            self.set_center_label("OK")
        else:
            self.set_center_label("ERR")

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
