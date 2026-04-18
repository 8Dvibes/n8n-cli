"""HTTP client for the n8n REST API. Zero external dependencies (urllib only)."""

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from .exceptions import N8nApiError, N8nConnectionError


class N8nClient:
    """Low-level REST client for the n8n public API."""

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        # Build a default SSL context
        self._ctx = ssl.create_default_context()

    def _headers(self, extra: Optional[dict] = None) -> dict:
        h = {
            "X-N8N-API-KEY": self.api_key,
            "Accept": "application/json",
        }
        if extra:
            h.update(extra)
        return h

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        body: Any = None,
        headers: Optional[dict] = None,
    ) -> Any:
        """Make an HTTP request and return parsed JSON (or None for 204)."""
        url = f"{self.api_url}{path}"

        if params:
            # Filter out None values
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                url += "?" + urllib.parse.urlencode(clean, doseq=True)

        data = None
        extra_headers = headers or {}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            extra_headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            url,
            data=data,
            headers=self._headers(extra_headers),
            method=method,
        )

        try:
            with urllib.request.urlopen(req, context=self._ctx, timeout=30) as resp:
                if resp.status == 204:
                    return None
                raw = resp.read().decode("utf-8")
                if not raw:
                    return None
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode("utf-8")
                err_body = json.loads(body_text)
            except Exception:
                err_body = body_text

            msg = body_text
            if isinstance(err_body, dict):
                msg = err_body.get("message", body_text)

            raise N8nApiError(e.code, msg, err_body) from e
        except urllib.error.URLError as e:
            raise N8nConnectionError(str(e.reason)) from e

    def get(self, path: str, params: Optional[dict] = None) -> Any:
        return self._request("GET", path, params=params)

    def post(self, path: str, body: Any = None, params: Optional[dict] = None) -> Any:
        return self._request("POST", path, params=params, body=body)

    def put(self, path: str, body: Any = None) -> Any:
        return self._request("PUT", path, body=body)

    def patch(self, path: str, body: Any = None) -> Any:
        return self._request("PATCH", path, body=body)

    def delete(self, path: str, params: Optional[dict] = None) -> Any:
        return self._request("DELETE", path, params=params)

    def paginate(self, path: str, params: Optional[dict] = None, limit: Optional[int] = None) -> list:
        """Auto-paginate a list endpoint using cursor-based pagination.

        Returns all items across pages. If limit is set, stops after
        collecting that many items.
        """
        all_items = []
        p = dict(params or {})
        p.setdefault("limit", 250)  # Max page size

        while True:
            resp = self.get(path, params=p)
            items = resp.get("data", [])
            all_items.extend(items)

            if limit and len(all_items) >= limit:
                return all_items[:limit]

            cursor = resp.get("nextCursor")
            if not cursor:
                break
            p["cursor"] = cursor

        return all_items
