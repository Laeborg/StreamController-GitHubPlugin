import requests
from loguru import logger as log

_BASE = "https://api.github.com"
_TIMEOUT = 10


class GitHubClient:
    def __init__(self, token: str):
        self._headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        }

    def get_pr_review_count(self) -> int:
        try:
            r = requests.get(
                f"{_BASE}/search/issues",
                headers=self._headers,
                params={"q": "is:pr is:open review-requested:@me", "per_page": 1},
                timeout=_TIMEOUT,
            )
            if r.status_code != 200:
                log.warning(f"GitHubPlugin: pr_review_count HTTP {r.status_code}")
                return 0
            return r.json().get("total_count", 0)
        except Exception as e:
            log.error(f"GitHubPlugin: get_pr_review_count: {e}")
            return 0

    def get_ci_failure_count(self) -> int:
        try:
            r = requests.get(
                f"{_BASE}/search/issues",
                headers=self._headers,
                params={"q": "is:pr is:open author:@me", "per_page": 20},
                timeout=_TIMEOUT,
            )
            if r.status_code != 200:
                return 0
            items = r.json().get("items", [])
            failures = 0
            for item in items:
                pr = item.get("pull_request")
                if not pr:
                    continue
                sha = pr.get("head", {}).get("sha") or item.get("head", {}).get("sha")
                if not sha:
                    continue
                # Extract owner/repo from html_url
                html_url = item.get("html_url", "")
                parts = html_url.replace("https://github.com/", "").split("/")
                if len(parts) < 2:
                    continue
                owner, repo = parts[0], parts[1]
                runs_r = requests.get(
                    f"{_BASE}/repos/{owner}/{repo}/commits/{sha}/check-runs",
                    headers=self._headers,
                    timeout=_TIMEOUT,
                )
                if runs_r.status_code != 200:
                    continue
                conclusions = [
                    run.get("conclusion")
                    for run in runs_r.json().get("check_runs", [])
                    if run.get("status") == "completed"
                ]
                if "failure" in conclusions:
                    failures += 1
            return failures
        except Exception as e:
            log.error(f"GitHubPlugin: get_ci_failure_count: {e}")
            return 0
