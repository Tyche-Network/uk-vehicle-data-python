"""UK vehicle data API client: DVLA vehicle enquiry and DVSA MOT history in one call.

Docs: https://api.tychelabs.net/docs/vehicle  Free key: https://api.tychelabs.net/signup
Standard library only (Python 3.9+).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterable, Optional

__all__ = ["VehicleData", "TycheApiError", "verify_webhook"]
__version__ = "1.0.0"


class TycheApiError(Exception):
    def __init__(self, status: int, code: str, message: str, body: Any = None):
        super().__init__(message)
        self.status, self.code, self.body = status, code, body


class _Client:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.tychelabs.net", timeout: float = 15.0):
        self.api_key = api_key or os.environ.get("TYCHE_API_KEY")
        if not self.api_key:
            raise ValueError("Pass api_key or set TYCHE_API_KEY. Free key: https://api.tychelabs.net/signup")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _req(self, method: str, path: str, body: Any = None) -> Any:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base_url + path, data=data, method=method)
        req.add_header("x-api-key", self.api_key)
        req.add_header("user-agent", f"tyche-python/{__version__}")
        if data is not None:
            req.add_header("content-type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as res:
                raw = res.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            try:
                j = json.loads(e.read() or b"{}")
            except ValueError:
                j = {}
            err = j.get("error") or {}
            raise TycheApiError(e.code, err.get("code", "http_error"), err.get("message", f"HTTP {e.code}"), j) from None

    def list_watches(self) -> Any:
        return self._req("GET", "/v1/watches")

    def delete_watch(self, watch_id: str) -> None:
        self._req("DELETE", "/v1/watches/" + urllib.parse.quote(watch_id, safe=""))

    def account(self) -> Any:
        return self._req("GET", "/v1/account")


class VehicleData(_Client):
    """Client for the UK vehicle data API.

    >>> api = VehicleData()            # reads TYCHE_API_KEY
    >>> v = api.lookup("AB12 CDE")["data"]
    >>> v["mot"]["expiryDate"], v["cleanAirZone"]["result"]
    """

    def lookup(self, registration: str) -> Any:
        return self._req("GET", "/v1/vehicles/" + urllib.parse.quote(registration, safe=""))

    def bulk(self, registrations: Iterable[str]) -> Any:
        return self._req("POST", "/v1/vehicles/bulk", {"registrations": list(registrations)})

    def watch(self, registration: str, url: str, days_before: Optional[list] = None) -> Any:
        return self._req("POST", "/v1/watches", {"registration": registration, "url": url, "daysBefore": days_before})


def verify_webhook(raw_body: bytes, header: str, secret: str, tolerance_secs: int = 300) -> bool:
    """Check the tyche-signature header of a webhook. raw_body must be the exact bytes received."""
    try:
        parts = dict(p.split("=", 1) for p in header.split(","))
        ts = int(parts["t"])
    except (KeyError, ValueError):
        return False
    if abs(time.time() - ts) > tolerance_secs:
        return False
    expected = hmac.new(secret.encode(), f"{ts}.".encode() + raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, parts.get("v1", ""))
