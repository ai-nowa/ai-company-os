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
import argparse
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
# Downloadables benefit（納品物添付）
#
# CEO 2026-05-25 判断: 実装・dry-run・検証ログまで着手可。
# 本番商品への benefit 作成・紐付け・checkout公開は T-046（キット5項目完成）
# とアオイ監査GO の後のみ。dry_run=True がデフォルト。
#
# フロー（Polar公式 API リファレンス 2026-05-25 実測）:
#   1. POST /v1/files/          納品ファイルのメタを登録 → presigned URL を取得
#   2. PUT  <presigned url>     各 part を S3 へアップロード（ETag を得る）
#   3. POST /v1/files/{id}/uploaded   アップロード完了をコミット
#   4. POST /v1/benefits/       type=downloadables, properties.files=[file_id]
#   5. POST /v1/products/{id}/benefits   商品へ benefit を紐付け
# ---------------------------------------------------------------------------

_BENEFIT_DESC_MIN = 3
_BENEFIT_DESC_MAX = 42
_DEFAULT_PART_SIZE = 50 * 1024 * 1024  # 50MB（S3マルチパート下限5MB以上・キットは1MB未満で単一part）


def _sha256_base64(data: bytes) -> str:
    import base64
    return base64.b64encode(hashlib.sha256(data).digest()).decode()


def _build_file_parts(data: bytes, part_size: int = _DEFAULT_PART_SIZE) -> list[dict]:
    """ファイルを part に分割し、各 part のメタ（番号・範囲・sha256）を作る。"""
    parts: list[dict] = []
    total = len(data)
    number = 1
    start = 0
    while start < total or (total == 0 and number == 1):
        end = min(start + part_size, total)
        parts.append({
            "number": number,
            "chunk_start": start,
            "chunk_end": end,
            "checksum_sha256_base64": _sha256_base64(data[start:end]),
        })
        if end >= total:
            break
        start = end
        number += 1
    return parts


def build_downloadable_payloads(file_path: str, description: str) -> dict[str, Any]:
    """納品ファイルから Files/Benefit 登録用ペイロードを構築する（ネットワーク非接続）。

    dry-run・検証ログ用。実 HTTP は送らない。
    """
    import mimetypes
    from pathlib import Path

    if not (_BENEFIT_DESC_MIN <= len(description) <= _BENEFIT_DESC_MAX):
        raise ValueError(
            f"description must be {_BENEFIT_DESC_MIN}-{_BENEFIT_DESC_MAX} chars (got {len(description)})"
        )
    path = Path(file_path)
    data = path.read_bytes()
    size = len(data)
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    parts = _build_file_parts(data)
    file_payload = {
        "name": path.name,
        "mime_type": mime_type,
        "size": size,
        "service": "downloadable",
        "checksum_sha256_base64": _sha256_base64(data),
        "upload": {"parts": parts},
    }
    # file_id は登録後に確定するため dry-run では占位子。
    benefit_payload = {
        "type": "downloadables",
        "description": description,
        "properties": {"files": ["<FILE_ID_AFTER_UPLOAD>"], "archived": {}},
    }
    return {
        "file_payload": file_payload,
        "benefit_payload": benefit_payload,
        "computed": {
            "size_bytes": size,
            "mime_type": mime_type,
            "part_count": len(parts),
            "sha256_base64": file_payload["checksum_sha256_base64"],
        },
    }


def create_file(file_payload: dict, sandbox: bool | None = None) -> dict:
    """POST /v1/files/ — 納品ファイルのメタ登録。presigned URL を含む応答を返す。"""
    return _post("/files/", file_payload, sandbox=sandbox)


def complete_file_upload(file_id: str, upload_id: str, parts: list[dict], path: str = "", sandbox: bool | None = None) -> dict:
    """POST /v1/files/{id}/uploaded — アップロード完了コミット。

    parts は [{number, checksum_etag, checksum_sha256_base64}]。
    NOTE: このエンドポイントは公式に個別ドキュメントが無く、Polar既知フローに基づく。
    ライブ実行前に必ず sandbox で疎通確認すること（CEOゲート: アオイGO後）。
    """
    body = {"id": upload_id, "path": path, "parts": parts}
    return _post(f"/files/{file_id}/uploaded", body, sandbox=sandbox)


def create_downloadable_benefit(benefit_payload: dict, sandbox: bool | None = None) -> dict:
    """POST /v1/benefits/ — downloadables benefit を作成。"""
    return _post("/benefits/", benefit_payload, sandbox=sandbox)


def attach_benefits_to_product(product_id: str, benefit_ids: list[str], sandbox: bool | None = None) -> dict:
    """POST /v1/products/{id}/benefits — 商品へ benefit を紐付け（既存も含む全集合を渡す）。"""
    return _post(f"/products/{product_id}/benefits", {"benefits": benefit_ids}, sandbox=sandbox)


def attach_downloadable_to_product(
    product_id: str,
    file_path: str,
    description: str,
    *,
    keep_existing_benefits: bool = True,
    dry_run: bool = True,
    sandbox: bool | None = None,
) -> dict[str, Any]:
    """納品ファイルを Polar 商品へ Downloadables として添付するオーケストレータ。

    dry_run=True（デフォルト）: ペイロードと既存 benefit を構築・取得して返すのみ（本番無変更）。
    dry_run=False: Files登録→アップロード→完了→Benefit作成→商品紐付け を実行。
                   ★ CEOゲート: T-046完成 + アオイGO 後、まず sandbox=True で実行すること。
    """
    payloads = build_downloadable_payloads(file_path, description)
    existing = [b.get("id") for b in get_product(product_id, sandbox=sandbox).get("benefits", []) if b.get("id")]

    if dry_run:
        return {
            "dry_run": True,
            "product_id": product_id,
            "existing_benefit_ids": existing,
            **payloads,
            "note": "本番無変更。ライブは dry_run=False + sandbox=True から。",
        }

    # --- ここから先は本番/サンドボックスを実際に変更する（CEOゲート後のみ） ---
    file_obj = create_file(payloads["file_payload"], sandbox=sandbox)
    upload = file_obj["upload"]
    etags: list[dict] = []
    data = __import__("pathlib").Path(file_path).read_bytes()
    for part in upload["parts"]:
        chunk = data[part["chunk_start"]:part["chunk_end"]]
        put = httpx.put(part["url"], content=chunk, headers=part.get("headers") or {}, timeout=120)
        put.raise_for_status()
        etags.append({
            "number": part["number"],
            "checksum_etag": put.headers.get("ETag", "").strip('"'),
            "checksum_sha256_base64": part["checksum_sha256_base64"],
        })
    complete_file_upload(file_obj["id"], upload["id"], etags, path=upload.get("path", ""), sandbox=sandbox)

    bp = dict(payloads["benefit_payload"])
    bp["properties"] = {"files": [file_obj["id"]], "archived": {}}
    benefit = create_downloadable_benefit(bp, sandbox=sandbox)

    benefit_ids = (existing if keep_existing_benefits else []) + [benefit["id"]]
    product = attach_benefits_to_product(product_id, benefit_ids, sandbox=sandbox)
    return {
        "dry_run": False,
        "file_id": file_obj["id"],
        "benefit_id": benefit["id"],
        "attached_benefit_ids": benefit_ids,
        "product_id": product.get("id", product_id),
    }


# ---------------------------------------------------------------------------
# Webhooks (HMAC-SHA256 verification)
# ---------------------------------------------------------------------------

def verify_webhook_signature(secret: str, body: bytes, signature_hex: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_hex)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Polar product/downloadable operations")
    sub = parser.add_subparsers(dest="command", required=True)

    products = sub.add_parser("products", help="List Polar products (read-only)")
    products.add_argument("--sandbox", action="store_true")

    payload = sub.add_parser("downloadable-payload", help="Build downloadable payload without network calls")
    payload.add_argument("--file", required=True)
    payload.add_argument("--description", default="AI NOWA OS Starter Kit v0.1")

    attach = sub.add_parser("attach-downloadable", help="Attach a downloadable benefit to a product")
    attach.add_argument("--product-id", required=True)
    attach.add_argument("--file", required=True)
    attach.add_argument("--description", default="AI NOWA OS Starter Kit v0.1")
    attach.add_argument("--sandbox", action="store_true")
    attach.add_argument("--live", action="store_true", help="Actually create/upload/attach instead of dry-run")
    attach.add_argument(
        "--confirm-production",
        default="",
        help="Required exact value CONFIRM_PRODUCTION_ATTACH when --live is used without --sandbox",
    )
    attach.add_argument("--replace-benefits", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "products":
        rows = []
        for p in list_products(sandbox=args.sandbox):
            rows.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "prices": p.get("prices", []),
                "benefit_count": len(p.get("benefits") or []),
                "is_archived": p.get("is_archived"),
            })
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    if args.command == "downloadable-payload":
        print(json.dumps(build_downloadable_payloads(args.file, args.description), ensure_ascii=False, indent=2))
        return 0

    if args.command == "attach-downloadable":
        if args.live and not args.sandbox and args.confirm_production != "CONFIRM_PRODUCTION_ATTACH":
            raise SystemExit(
                "Production attach requires --confirm-production CONFIRM_PRODUCTION_ATTACH. "
                "Run sandbox live first, then production after audit GO."
            )
        result = attach_downloadable_to_product(
            args.product_id,
            args.file,
            args.description,
            keep_existing_benefits=not args.replace_benefits,
            dry_run=not args.live,
            sandbox=args.sandbox,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
