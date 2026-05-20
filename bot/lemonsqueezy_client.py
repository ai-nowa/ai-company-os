"""Lemon Squeezy API ラッパー。
test/live は API Key で分けない仕様（Stripe と違う）。
商品 test_mode は variants 作成時に指定する。
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any

import httpx

BASE_URL = "https://api.lemonsqueezy.com/v1"
STORE_ID = "379291"


def _api_key() -> str:
    key = os.environ.get("LEMONSQUEEZY_API_KEY", "")
    if not key:
        raise RuntimeError("LEMONSQUEEZY_API_KEY not set")
    return key


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
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
# Store
# ---------------------------------------------------------------------------

def get_store() -> dict:
    return _get(f"/stores/{STORE_ID}")


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

def list_products() -> list[dict]:
    data = _get("/products", {"filter[store_id]": STORE_ID})
    return data.get("data", [])


def create_product(name: str, slug: str, description: str = "") -> dict:
    body = {
        "data": {
            "type": "products",
            "attributes": {
                "name": name,
                "slug": slug,
                "description": description,
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": STORE_ID}},
            },
        }
    }
    return _post("/products", body)


# ---------------------------------------------------------------------------
# Variants
# ---------------------------------------------------------------------------

def list_variants(product_id: str) -> list[dict]:
    data = _get("/variants", {"filter[product_id]": product_id})
    return data.get("data", [])


def create_variant(
    product_id: str,
    name: str,
    price: int,
    *,
    test_mode: bool = True,
    description: str = "",
) -> dict:
    """
    price は日本円（整数）。
    test_mode=True の間は審査前でもテスト購入可能。
    本番審査完了後に False に切り替える。
    """
    body = {
        "data": {
            "type": "variants",
            "attributes": {
                "name": name,
                "description": description,
                "price": price,
                "is_subscription": False,
                "test_mode": test_mode,
            },
            "relationships": {
                "product": {"data": {"type": "products", "id": product_id}},
            },
        }
    }
    return _post("/variants", body)


def update_variant_test_mode(variant_id: str, test_mode: bool) -> dict:
    body = {
        "data": {
            "type": "variants",
            "id": variant_id,
            "attributes": {"test_mode": test_mode},
        }
    }
    return _patch(f"/variants/{variant_id}", body)


# ---------------------------------------------------------------------------
# Checkouts
# ---------------------------------------------------------------------------

def create_checkout(
    variant_id: str,
    *,
    email: str = "",
    custom_data: dict | None = None,
    expires_at: str | None = None,
    button_color: str = "#18181b",
    test_mode: bool = True,
) -> str:
    """Checkout URL を返す。"""
    attrs: dict[str, Any] = {
        "checkout_options": {
            "embed": False,
            "media": True,
            "logo": True,
            "desc": True,
            "discount": True,
            "dark": True,
            "button_color": button_color,
        },
        "checkout_data": {
            "custom": custom_data or {},
        },
        "test_mode": test_mode,
    }
    if email:
        attrs["checkout_data"]["email"] = email
    if expires_at:
        attrs["expires_at"] = expires_at

    body = {
        "data": {
            "type": "checkouts",
            "attributes": attrs,
            "relationships": {
                "store": {"data": {"type": "stores", "id": STORE_ID}},
                "variant": {"data": {"type": "variants", "id": variant_id}},
            },
        }
    }
    resp = _post("/checkouts", body)
    return resp["data"]["attributes"]["url"]


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

def list_orders(page: int = 1) -> list[dict]:
    data = _get("/orders", {"filter[store_id]": STORE_ID, "page[number]": page})
    return data.get("data", [])


def get_order(order_id: str) -> dict:
    return _get(f"/orders/{order_id}")


# ---------------------------------------------------------------------------
# License Keys
# ---------------------------------------------------------------------------

def list_license_keys(order_id: str | None = None) -> list[dict]:
    params: dict = {"filter[store_id]": STORE_ID}
    if order_id:
        params["filter[order_id]"] = order_id
    data = _get("/license-keys", params)
    return data.get("data", [])


def get_license_key(key_id: str) -> dict:
    return _get(f"/license-keys/{key_id}")


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

def list_webhooks() -> list[dict]:
    data = _get("/webhooks", {"filter[store_id]": STORE_ID})
    return data.get("data", [])


def create_webhook(url: str, events: list[str], secret: str) -> dict:
    body = {
        "data": {
            "type": "webhooks",
            "attributes": {
                "url": url,
                "events": events,
                "secret": secret,
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": STORE_ID}},
            },
        }
    }
    return _post("/webhooks", body)


def verify_webhook_signature(payload_bytes: bytes, signature_header: str, secret: str) -> bool:
    """X-Signature ヘッダーの HMAC-SHA256 を検証する。"""
    expected = hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


