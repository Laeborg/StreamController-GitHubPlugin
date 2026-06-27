import threading
from loguru import logger as log

from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.PluginManager.ActionInputSupport import ActionInputSupport
from src.backend.DeckManagement.InputIdentifier import Input

from .github_client import GitHubClient
from .actions.PRReviewCountAction import PRReviewCountAction
from .actions.CIStatusAction import CIStatusAction
from .actions.ScreenSummaryAction import ScreenSummaryAction
from .actions.OpenGitHubAction import OpenGitHubAction
from .actions.GHCommandAction import GHCommandAction
from .actions.TouchKeyStatusAction import TouchKeyStatusAction

POLL_INTERVAL = 60  # seconds


class GitHubPlugin(PluginBase):
    def __init__(self):
        super().__init__()

        self.cache = {
            "pr_review_count": 0,
            "ci_failure_count": 0,
            "last_error": None,
        }
        self._poll_thread = None
        self._stop_event = threading.Event()
        self._polling = threading.Event()

        key_only = {
            Input.Key: ActionInputSupport.SUPPORTED,
            Input.Dial: ActionInputSupport.UNSUPPORTED,
            Input.Touchscreen: ActionInputSupport.UNSUPPORTED,
            Input.TouchKey: ActionInputSupport.UNSUPPORTED,
            Input.Screen: ActionInputSupport.UNSUPPORTED,
        }
        touch_key_only = {
            Input.Key: ActionInputSupport.UNSUPPORTED,
            Input.Dial: ActionInputSupport.UNSUPPORTED,
            Input.Touchscreen: ActionInputSupport.UNSUPPORTED,
            Input.TouchKey: ActionInputSupport.SUPPORTED,
            Input.Screen: ActionInputSupport.UNSUPPORTED,
        }
        screen_only = {
            Input.Key: ActionInputSupport.UNSUPPORTED,
            Input.Dial: ActionInputSupport.UNSUPPORTED,
            Input.Touchscreen: ActionInputSupport.UNSUPPORTED,
            Input.TouchKey: ActionInputSupport.UNSUPPORTED,
            Input.Screen: ActionInputSupport.SUPPORTED,
        }

        self.add_action_holders([
            ActionHolder(plugin_base=self, action_base=PRReviewCountAction,
                         action_id_suffix="PRReviewCount", action_name="PR Review Count",
                         action_support=key_only),
            ActionHolder(plugin_base=self, action_base=CIStatusAction,
                         action_id_suffix="CIStatus", action_name="CI Failure Count",
                         action_support=key_only),
            ActionHolder(plugin_base=self, action_base=ScreenSummaryAction,
                         action_id_suffix="ScreenSummary", action_name="Screen Summary",
                         action_support=screen_only),
            ActionHolder(plugin_base=self, action_base=OpenGitHubAction,
                         action_id_suffix="OpenGitHub", action_name="Open GitHub",
                         action_support=key_only),
            ActionHolder(plugin_base=self, action_base=GHCommandAction,
                         action_id_suffix="GHCommand", action_name="gh CLI Command",
                         action_support=key_only),
            ActionHolder(plugin_base=self, action_base=TouchKeyStatusAction,
                         action_id_suffix="TouchKeyStatus", action_name="Touch Key Status LED",
                         action_support=touch_key_only),
        ])

        self.register(
            plugin_name="GitHub Plugin (Laeborg)",
            github_repo="https://github.com/laeborg/StreamController-GitHubPlugin",
            plugin_version="0.1.0",
            app_version="1.5.0-beta.14",
        )

        self._start_poll_thread()

    def _get_client(self):
        token = self.get_settings().get("github_token", "")
        if not token:
            return None
        return GitHubClient(token)

    def _start_poll_thread(self):
        self._stop_event.clear()
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def _poll_loop(self):
        while not self._stop_event.is_set():
            self._do_poll()
            self._stop_event.wait(POLL_INTERVAL)

    def _do_poll(self):
        self._polling.set()
        try:
            client = self._get_client()
            if client is None:
                return
            # Assemble new cache dict, then atomic replacement (CPython dict assignment is GIL-protected)
            new_cache = {
                "pr_review_count": client.get_pr_review_count(),
                "ci_failure_count": client.get_ci_failure_count(),
                "last_error": None,
            }
            self.cache = new_cache
            log.info(f"GitHubPlugin: cache updated: {self.cache}")
        finally:
            self._polling.clear()

    def force_poll(self):
        if self._polling.is_set():
            return
        threading.Thread(target=self._do_poll, daemon=True).start()

    def on_uninstall(self):
        self._stop_event.set()
        super().on_uninstall()
