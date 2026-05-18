"""Polar.sh API ラッパー（Lemon Squeezy 撤退・Polar.sh 採用 2026-05-18 CEO決定）。

API base: https://api.polar.sh/v1
Auth: Bearer <POLAR_API_KEY>  (Organization Access Token)
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any

import httpx

BASE_URL = "https://api.polar.sh/v1"
ORG_ID = "676275d5-a3c5-4f89-81ba-97859a62eeeb"  # ai-nowa


def _api_key() -> str:
    key = os.environ.get("POLAR_API_KEY", "")
    if not key:
        raise RuntimeError("POLAR_API_KEY not set")
    return key


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _get(path: str, params: dict | None = None) -> dict:
    r = httpx.get(f"{BASE_URL}{path}", headers=_headers(), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def _post(path: str, body: dict) -> dict:
    r = httpx.post(f"{BASE_URL}{path}", headers=_headers(), json=body, timeout=30)
    r.raise_for_status()
    return r.json()


def _patch(path: str, body: dict) -> dict:
    r = httpx.patch(f"{BASE_URL}{path}", headers=_headers(), json=body, timeout=30)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------

def list_organizations() -> list[dict]:
    data = _get("/organizations/")
    return data.get("items", [])


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

def list_products(organization_id: str = ORG_ID) -> list[dict]:
    data = _get("/products/", {"organization_id": organization_id})
    return data.get("items", [])


def create_product(
    name: str,
    price_amount: int,
    *,
    description: str = "",
    price_currency: str = "jpy",
) -> dict:
    """One-time product を作成。price_amount は最小単位（JPYなら円）。

    Note: Organization Access Token 使用時は organization_id 指定禁止
    （422 PolarRequestValidationError: organization_token）。
    """
    body = {
        "name": name,
        "description": description,
        "prices": [
            {
                "amount_type": "fixed",
                "price_currency": price_currency,
                "price_amount": price_amount,
            }
        ],
        "recurring_interval": None,
    }
    return _post("/products/", body)


def get_product(product_id: str) -> dict:
    return _get(f"/products/{product_id}")


# ---------------------------------------------------------------------------
# Checkouts
# ---------------------------------------------------------------------------

def create_checkout(
    product_id: str,
    *,
    customer_email: str | None = None,
    success_url: str | None = None,
    metadata: dict | None = None,
) -> dict:
    body: dict[str, Any] = {"products": [product_id]}
    if customer_email:
        body["customer_email"] = customer_email
    if success_url:
        body["success_url"] = success_url
    if metadata:
        body["metadata"] = metadata
    return _post("/checkouts/", body)


# ---------------------------------------------------------------------------
# Webhooks (HMAC-SHA256 verification)
# ---------------------------------------------------------------------------

def verify_webhook_signature(secret: str, body: bytes, signature_hex: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_hex)
