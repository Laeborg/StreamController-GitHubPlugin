import subprocess
from src.backend.PluginManager.ActionCore import ActionCore


class OpenGitHubAction(ActionCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        self.set_center_label("GitHub")
        self.set_background_color([20, 20, 20, 255])

    def on_key_down(self):
        settings = self.get_settings()
        url = settings.get("url", "https://github.com")
        try:
            subprocess.run(["xdg-open", url], timeout=5)
        except subprocess.TimeoutExpired:
            pass

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
