import pytest
from unittest.mock import patch, MagicMock
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from github_client import GitHubClient


def _mock_response(json_data, status_code=200):
    m = MagicMock()
    m.status_code = status_code
    m.json.return_value = json_data
    return m


class TestGetPRReviewCount:
    def test_returns_total_count(self):
        client = GitHubClient(token="tok")
        with patch("github_client.requests.get") as mock_get:
            mock_get.return_value = _mock_response({"total_count": 3, "items": []})
            assert client.get_pr_review_count() == 3

    def test_returns_zero_on_auth_error(self):
        client = GitHubClient(token="bad")
        with patch("github_client.requests.get") as mock_get:
            mock_get.return_value = _mock_response({}, 401)
            assert client.get_pr_review_count() == 0

    def test_returns_zero_on_network_error(self):
        client = GitHubClient(token="tok")
        with patch("github_client.requests.get", side_effect=Exception("timeout")):
            assert client.get_pr_review_count() == 0


class TestGetCIFailureCount:
    def test_returns_failure_count(self):
        client = GitHubClient(token="tok")
        prs_response = {
            "total_count": 1,
            "items": [
                {
                    "html_url": "https://github.com/laeborg/repo/pull/1",
                    "pull_request": {"head": {"sha": "abc123"}},
                }
            ],
        }
        runs_response = {
            "check_runs": [
                {"status": "completed", "conclusion": "failure"},
                {"status": "completed", "conclusion": "success"},
            ]
        }
        with patch("github_client.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response(prs_response),
                _mock_response(runs_response),
            ]
            assert client.get_ci_failure_count() == 1

    def test_returns_zero_when_all_pass(self):
        client = GitHubClient(token="tok")
        prs_response = {
            "total_count": 1,
            "items": [
                {
                    "html_url": "https://github.com/laeborg/repo/pull/1",
                    "pull_request": {"head": {"sha": "abc123"}},
                }
            ],
        }
        runs_response = {
            "check_runs": [{"status": "completed", "conclusion": "success"}]
        }
        with patch("github_client.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response(prs_response),
                _mock_response(runs_response),
            ]
            assert client.get_ci_failure_count() == 0
