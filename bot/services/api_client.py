"""
LMS API client.

Handles all HTTP requests to the LMS backend with proper error handling.
This is a *service layer* — isolated from handlers and Telegram.
"""

import httpx
from config import load_config


class LMSClient:
    """Client for the LMS backend API."""

    def __init__(self):
        config = load_config()
        self.base_url = config["LMS_API_BASE_URL"]
        self.api_key = config["LMS_API_KEY"]
        self._headers = {"Authorization": f"Bearer {self.api_key}"}

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict | list | None:
        """
        Make an HTTP request to the backend.

        Returns the parsed JSON response, or None on error.
        Raises an exception with a user-friendly message on failure.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            with httpx.Client() as client:
                response = client.request(method, url, headers=self._headers, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Backend error: connection refused ({self.base_url}). "
                "Check that the services are running."
            ) from e
        except httpx.HTTPStatusError as e:
            raise ConnectionError(
                f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. "
                "The backend service may be down."
            ) from e
        except httpx.HTTPError as e:
            raise ConnectionError(
                f"Backend error: {str(e)}. Check the backend configuration."
            ) from e

    def get_items(self) -> list:
        """Get all items (labs and tasks)."""
        result = self._make_request("GET", "/items/")
        return result if isinstance(result, list) else []

    def get_pass_rates(self, lab: str) -> list:
        """Get pass rates for a specific lab."""
        result = self._make_request("GET", f"/analytics/pass-rates?lab={lab}")
        return result if isinstance(result, list) else []

    def get_learners(self) -> list:
        """Get all enrolled learners."""
        result = self._make_request("GET", "/learners/")
        return result if isinstance(result, list) else []

    def get_analytics(self, endpoint: str, **params) -> dict | list:
        """Generic analytics endpoint accessor."""
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"/analytics/{endpoint}"
        if query:
            url += f"?{query}"
        return self._make_request("GET", url)

    def sync_pipeline(self) -> dict:
        """Trigger ETL sync."""
        return self._make_request("POST", "/pipeline/sync", json={})
