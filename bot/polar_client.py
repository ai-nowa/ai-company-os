"""Polar.sh API ラッパー（Lemon Squeezy 撤退・Polar.sh 採用 2026-05-18 CEO決定）。

API base:
  Production: https://api.polar.sh/v1
  Sandbox:    https://sandbox-api.polar.sh/v1

Auth: Bearer <POLAR_API_KEY>  (Organization Access Token)
環境変数 POLAR_SANDBOX=1 または sandbox=True 引数でSandbox切替。
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any

import httpx

_PROD_URL = "https://api.polar.sh/v1"
_SANDBOX_URL = "https://sandbox-api.polar.sh/v1"
ORG_ID = "676275d5-a3c5-4f89-81ba-97859a62eeeb"  # ai-nowa


def _is_sandbox() -> bool:
    return os.environ.get("POLAR_SANDBOX", "").strip() in ("1", "true", "yes")


def _base_url(sandbox: bool | None = None) -> str:
    use_sandbox = sandbox if sandbox is not None else _is_sandbox()
    return _SANDBOX_URL if use_sandbox else _PROD_URL


def _api_key(sandbox: bool | None = None) -> str:
    use_sandbox = sandbox if sandbox is not None else _is_sandbox()
    env_var = "POLAR_API_KEY_SANDBOX" if use_sandbox else "POLAR_API_KEY"
    key = os.environ.get(env_var, "")
    if not key:
        raise RuntimeError(f"{env_var} not set")
    return key


def _headers(sandbox: bool | None = None) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_api_key(sandbox)}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _get(path: str, params: dict | None = None, sandbox: bool | None = None) -> dict:
    r = httpx.get(f"{_base_url(sandbox)}{path}", headers=_headers(sandbox), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def _post(path: str, body: dict, sandbox: bool | None = None) -> dict:
    r = httpx.post(f"{_base_url(sandbox)}{path}", headers=_headers(sandbox), json=body, timeout=30)
    r.raise_for_status()
    return r.json()


def _patch(path: str, body: dict, sandbox: bool | None = None) -> dict:
    r = httpx.patch(f"{_base_url(sandbox)}{path}", headers=_headers(sandbox), json=body, timeout=30)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------

def list_organizations(sandbox: bool | None = None) -> list[dict]:
    data = _get("/organizations/", sandbox=sandbox)
    return data.get("items", [])


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

def list_products(organization_id: str = ORG_ID, sandbox: bool | None = None) -> list[dict]:
    data = _get("/products/", {"organization_id": organization_id}, sandbox=sandbox)
    return data.get("items", [])


def create_product(
    name: str,
    price_amount: int,
    *,
    description: str = "",
    price_currency: str = "jpy",
    sandbox: bool | None = None,
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
    return _post("/products/", body, sandbox=sandbox)


def get_product(product_id: str, sandbox: bool | None = None) -> dict:
    return _get(f"/products/{product_id}", sandbox=sandbox)


# ---------------------------------------------------------------------------
# Checkouts
# ---------------------------------------------------------------------------

def create_checkout(
    product_id: str | None = None,
    *,
    products: list[str] | None = None,
    product_price_id: str | None = None,
    customer_email: str | None = None,
    success_url: str | None = None,
    metadata: dict | None = None,
    sandbox: bool | None = None,
) -> dict:
    """Checkout セッションを作成。

    Polar の現行 API は `products: [product_id, ...]` が必須。
    旧 `product_price_id` は deprecated かつ Product ID と別物なので、誤用を避ける。
    """
    if product_price_id:
        raise ValueError("product_price_id is deprecated; pass product_id or products instead")
    checkout_products = products or ([product_id] if product_id else [])
    if not checkout_products:
        raise ValueError("product_id or products is required")
    body: dict[str, Any] = {"products": checkout_products}
    if customer_email:
        body["customer_email"] = customer_email
    if success_url:
        body["success_url"] = success_url
    if metadata:
        body["metadata"] = metadata
    return _post("/checkouts/", body, sandbox=sandbox)


# ---------------------------------------------------------------------------
# Webhooks (HMAC-SHA256 verification)
# ---------------------------------------------------------------------------

def verify_webhook_signature(secret: str, body: bytes, signature_hex: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_hex)
