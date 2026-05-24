"""External business metrics for AI NOWA.

This module is the single integration point between external observations and
employee decision-making.  A missing API or permission is reported as
``available: false``; it is never silently converted into a business zero.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
import requests

from .config import BASE_DIR, COMPANY_DIR, JST, now_jst_iso

SNAPSHOT_PATH = COMPANY_DIR / "external_metrics_snapshot.json"
HISTORY_PATH = COMPANY_DIR / "external_metrics.jsonl"
KPI_OBSERVATIONS_PATH = COMPANY_DIR / "kpi_observations.md"
HISTORY_MAX_LINES = 1000

SHOP_URL = "https://ai-nowa.com/shop/"
HOME_URL = "https://ai-nowa.com/"
PURCHASE_INTENT_WORKER_URL = "https://ai-nowa-purchase-intent.shogun-army.workers.dev"


def _ok(source: str, **data: Any) -> dict[str, Any]:
    return {"available": True, "source": source, **data}


def _unavailable(source: str, reason: str, **data: Any) -> dict[str, Any]:
    return {"available": False, "source": source, "unavailable_reason": reason, **data}


def _short_error(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}"
    text = re.sub(r"\s+", " ", text).strip()
    return text[:240]


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(JST)
    except ValueError:
        return None


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _token_path(env_value: str | None, default: Path) -> Path:
    raw = env_value or str(default)
    path = Path(raw)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


def _parse_google_expiry(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return (
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            .astimezone(timezone.utc)
            .replace(tzinfo=None)
        )
    except ValueError:
        return None


def _write_refreshed_token(token_path: Path, original: dict[str, Any], creds: Any) -> None:
    updated = dict(original)
    updated["token"] = creds.token
    if creds.refresh_token:
        updated["refresh_token"] = creds.refresh_token
    if creds.expiry:
        expiry = creds.expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        else:
            expiry = expiry.astimezone(timezone.utc)
        updated["expiry"] = expiry.isoformat().replace("+00:00", "Z")
    if creds.scopes:
        updated["scopes"] = list(creds.scopes)
    token_path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _credentials_from_token(token_path: Path, scopes: list[str] | None = None):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    token = _read_json(token_path)
    if not token:
        raise RuntimeError(f"token file not found or invalid: {token_path}")
    requested_scopes = scopes or token.get("scopes")
    creds = Credentials(
        token=token.get("token"),
        refresh_token=token.get("refresh_token"),
        token_uri=token.get("token_uri"),
        client_id=token.get("client_id"),
        client_secret=token.get("client_secret"),
        scopes=requested_scopes,
        expiry=_parse_google_expiry(token.get("expiry")),
    )
    if creds.refresh_token and (not creds.token or not creds.valid or creds.expiry is None or creds.expired):
        creds.refresh(Request())
        _write_refreshed_token(token_path, token, creds)
    if not creds.valid:
        raise RuntimeError("OAuth credentials are not valid after refresh")
    return creds


def collect_cognition() -> dict[str, Any]:
    try:
        from .cognition_metrics import fetch_cognition_metrics

        raw = fetch_cognition_metrics()
        github = raw.get("github", {})
        zenn = raw.get("zenn", {})
        hatena = raw.get("hatena", {})
        return _ok(
            "cognition_metrics.py",
            stars=github.get("stars", 0),
            forks=github.get("forks", 0),
            zenn_liked=zenn.get("total_liked", 0),
            zenn_articles=len(zenn.get("articles", [])),
            zenn_books=len(zenn.get("books", [])),
            hatena_bookmarks=hatena.get("total_bookmarks", 0),
        )
    except Exception as exc:
        return _unavailable(
            "cognition_metrics.py",
            _short_error(exc),
            stars=0,
            forks=0,
            zenn_liked=0,
            zenn_articles=0,
            zenn_books=0,
            hatena_bookmarks=0,
        )


def collect_revenue() -> dict[str, Any]:
    try:
        from . import polar_client

        polar_client._api_key()
        data = polar_client._get("/orders/", params={"limit": 100})
        items = data.get("items", [])
        total = sum(int(order.get("amount", 0) or 0) for order in items)
        latest_ts = ""
        for order in items:
            ts = str(order.get("created_at") or order.get("createdAt") or "")
            if ts > latest_ts:
                latest_ts = ts
        return _ok(
            "polar_api",
            order_count=len(items),
            gross_jpy=total,
            latest_order_ts=latest_ts or None,
        )
    except Exception as exc:
        return _unavailable("polar_api", _short_error(exc), order_count=None, gross_jpy=None)


def collect_ga4() -> dict[str, Any]:
    property_id = os.environ.get("GA4_PROPERTY_ID", "").strip()
    token_path = _token_path(os.environ.get("GA4_TOKEN_JSON"), BASE_DIR / "bot" / "ga4_token.json")
    if not property_id:
        return _unavailable("ga4", "GA4_PROPERTY_ID is not set")
    if not token_path.exists():
        return _unavailable("ga4", f"token file does not exist: {token_path}")
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest

        creds = _credentials_from_token(
            token_path,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"],
        )
        client = BetaAnalyticsDataClient(credentials=creds)
        req = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date="today", end_date="today")],
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="screenPageViews"), Metric(name="activeUsers")],
            limit=50,
        )
        response = client.run_report(req)
        pages: list[dict[str, Any]] = []
        total_views = 0
        active_users = 0
        shop_views = 0
        about_views = 0
        for row in response.rows:
            path = row.dimension_values[0].value
            views = int(row.metric_values[0].value or 0)
            users = int(row.metric_values[1].value or 0)
            total_views += views
            active_users += users
            if path.startswith("/shop"):
                shop_views += views
            if path.startswith("/about"):
                about_views += views
            pages.append({"path": path, "views": views, "active_users": users})
        pages.sort(key=lambda p: p["views"], reverse=True)
        return _ok(
            "ga4_data_api",
            property_id=property_id,
            pageviews_today=total_views,
            active_users_today=active_users,
            shop_pageviews_today=shop_views,
            about_pageviews_today=about_views,
            top_pages_today=pages[:8],
        )
    except Exception as exc:
        return _unavailable("ga4_data_api", _short_error(exc), property_id=property_id)


def collect_youtube() -> dict[str, Any]:
    token_path = _token_path(os.environ.get("YOUTUBE_TOKEN_FILE"), BASE_DIR / "bot" / "youtube_token.json")
    if not token_path.exists():
        return _unavailable("youtube_data_api", f"token file does not exist: {token_path}")
    try:
        from googleapiclient.discovery import build

        token = _read_json(token_path)
        scopes = set(token.get("scopes") or [])
        accepted_scopes = {
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/youtube.force-ssl",
        }
        if not scopes.intersection(accepted_scopes):
            return _unavailable(
                "youtube_data_api",
                "youtube_token.json lacks youtube.readonly scope; reauthorize with channel read scope",
            )
        creds = _credentials_from_token(token_path)
        service = build("youtube", "v3", credentials=creds, cache_discovery=False)
        response = service.channels().list(part="snippet,statistics", mine=True).execute()
        items = response.get("items", [])
        if not items:
            return _unavailable("youtube_data_api", "channels.list returned no channel")
        channel = items[0]
        stats = channel.get("statistics", {})
        snippet = channel.get("snippet", {})
        return _ok(
            "youtube_data_api",
            channel_title=snippet.get("title", ""),
            subscriber_count=_safe_int(stats.get("subscriberCount")),
            view_count=_safe_int(stats.get("viewCount")),
            video_count=_safe_int(stats.get("videoCount")),
        )
    except Exception as exc:
        return _unavailable("youtube_data_api", _short_error(exc))


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _kv_namespace_id() -> str:
    path = BASE_DIR / "workers" / "purchase-intent" / "wrangler.toml"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    match = re.search(r'binding\s*=\s*"PURCHASE_INTENT".*?id\s*=\s*"([^"]+)"', text, re.S)
    return match.group(1) if match else ""


def _count_intent_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now(JST)
    cutoff_24h = now - timedelta(hours=24)
    counts = {"yes": 0, "maybe": 0, "other": 0}
    recent_24h = 0
    latest_ts = ""
    for entry in entries:
        intent = str(entry.get("intent", "")).lower()
        if intent in counts:
            counts[intent] += 1
        else:
            counts["other"] += 1
        ts = str(entry.get("ts") or "")
        dt = _parse_dt(ts)
        if dt and dt >= cutoff_24h:
            recent_24h += 1
        if ts > latest_ts:
            latest_ts = ts
    return {
        "total": len(entries),
        "yes": counts["yes"],
        "maybe": counts["maybe"],
        "other": counts["other"],
        "recent_24h": recent_24h,
        "latest_ts": latest_ts or None,
        "contains_pii": False,
    }


def collect_purchase_intent() -> dict[str, Any]:
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    namespace_id = _kv_namespace_id()
    if not account_id:
        return _unavailable("cloudflare_kv_purchase_intent", "CLOUDFLARE_ACCOUNT_ID is not set")
    if not token:
        return _unavailable("cloudflare_kv_purchase_intent", "CLOUDFLARE_API_TOKEN is not set")
    if not namespace_id:
        return _unavailable("cloudflare_kv_purchase_intent", "PURCHASE_INTENT KV namespace id not found")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        base = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/storage/kv/namespaces/{namespace_id}"
        keys: list[str] = []
        cursor = ""
        with httpx.Client(timeout=20) as client:
            while True:
                params = {"limit": 1000}
                if cursor:
                    params["cursor"] = cursor
                res = client.get(f"{base}/keys", headers=headers, params=params)
                res.raise_for_status()
                payload = res.json()
                if not payload.get("success", False):
                    return _unavailable("cloudflare_kv_purchase_intent", "Cloudflare keys API returned success=false")
                keys.extend(k["name"] for k in payload.get("result", []))
                cursor = payload.get("result_info", {}).get("cursor") or ""
                if not cursor:
                    break

            entries: list[dict[str, Any]] = []
            for key in keys[:1000]:
                res = client.get(f"{base}/values/{key}", headers=headers)
                res.raise_for_status()
                try:
                    value = res.json()
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    # Keep only non-PII fields.
                    entries.append({"intent": value.get("intent"), "ts": value.get("ts")})
        counts = _count_intent_entries(entries)
        return _ok("cloudflare_kv_purchase_intent", **counts)
    except Exception as exc:
        return _unavailable("cloudflare_kv_purchase_intent", _short_error(exc))


def _fetch_text(url: str) -> str:
    res = requests.get(url, headers={"User-Agent": "ai-nowa-metrics/1.0"}, timeout=15)
    res.raise_for_status()
    return res.text


def _extract_price(text: str) -> str | None:
    match = re.search(r"¥\s*([0-9,]+)", text)
    return f"¥{match.group(1)}" if match else None


def _extract_title(text: str) -> str | None:
    match = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip()


def collect_site_state() -> dict[str, Any]:
    data: dict[str, Any] = {}
    try:
        shop_live = _fetch_text(SHOP_URL)
        data["shop_live"] = {
            "available": True,
            "url": SHOP_URL,
            "title": _extract_title(shop_live),
            "price": _extract_price(shop_live),
            "has_intent_anchor": "#intent-form" in shop_live or "意向を送る" in shop_live,
            "has_mailto": "mailto:" in shop_live or "/cdn-cgi/l/email-protection" in shop_live,
            "has_ga4_tag": "googletagmanager.com/gtag/js" in shop_live or "gtag(" in shop_live,
        }
    except Exception as exc:
        data["shop_live"] = _unavailable("public_http", _short_error(exc), url=SHOP_URL)

    try:
        home_live = _fetch_text(HOME_URL)
        data["home_live"] = {
            "available": True,
            "url": HOME_URL,
            "title": _extract_title(home_live),
            "has_ga4_tag": "googletagmanager.com/gtag/js" in home_live or "gtag(" in home_live,
        }
    except Exception as exc:
        data["home_live"] = _unavailable("public_http", _short_error(exc), url=HOME_URL)

    local_shop = BASE_DIR / "site" / "public" / "shop" / "index.html"
    if local_shop.exists():
        text = local_shop.read_text(encoding="utf-8", errors="replace")
        data["shop_local"] = {
            "available": True,
            "path": str(local_shop.relative_to(BASE_DIR)),
            "title": _extract_title(text),
            "price": _extract_price(text),
            "has_intent_anchor": "#intent-form" in text or "意向を送る" in text,
            "has_mailto": "mailto:" in text,
            "has_ga4_tag": "googletagmanager.com/gtag/js" in text or "gtag(" in text,
        }

    live = data.get("shop_live", {})
    local = data.get("shop_local", {})
    data["shop_local_live_mismatch"] = bool(
        live.get("available")
        and local.get("available")
        and (
            live.get("title") != local.get("title")
            or live.get("price") != local.get("price")
            or live.get("has_intent_anchor") != local.get("has_intent_anchor")
        )
    )
    return data


def collect_external_metrics() -> dict[str, Any]:
    metrics = {
        "ts": now_jst_iso(),
        "cognition": collect_cognition(),
        "revenue": collect_revenue(),
        "traffic": {"ga4": collect_ga4()},
        "youtube": collect_youtube(),
        "intent": {"purchase_form": collect_purchase_intent()},
        "site": collect_site_state(),
    }
    metrics["health"] = _source_health(metrics)
    return metrics


def _source_health(metrics: dict[str, Any]) -> dict[str, Any]:
    sources = {
        "cognition": metrics.get("cognition", {}),
        "revenue": metrics.get("revenue", {}),
        "ga4": metrics.get("traffic", {}).get("ga4", {}),
        "youtube": metrics.get("youtube", {}),
        "intent_form": metrics.get("intent", {}).get("purchase_form", {}),
        "shop_live": metrics.get("site", {}).get("shop_live", {}),
    }
    unavailable = {
        name: src.get("unavailable_reason", "unknown")
        for name, src in sources.items()
        if src and src.get("available") is False
    }
    return {
        "all_available": not unavailable,
        "unavailable": unavailable,
        "shop_local_live_mismatch": metrics.get("site", {}).get("shop_local_live_mismatch", False),
    }


def write_external_metrics_snapshot(metrics: dict[str, Any]) -> None:
    COMPANY_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    with HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(metrics, ensure_ascii=False) + "\n")
    try:
        lines = HISTORY_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
        if len(lines) > HISTORY_MAX_LINES:
            HISTORY_PATH.write_text("\n".join(lines[-HISTORY_MAX_LINES:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def load_latest_external_metrics() -> dict[str, Any]:
    data = _read_json(SNAPSHOT_PATH)
    if data:
        return data
    state = _read_json(COMPANY_DIR / ".self_improvement_state.json")
    snapshots = state.get("snapshots", [])
    if snapshots:
        latest = snapshots[-1].get("external", {})
        if latest:
            return latest
    return {}


def _value(value: Any, fallback: str = "未取得") -> str:
    if value is None or value == "":
        return fallback
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def external_digest_items(max_items: int = 8) -> list[str]:
    metrics = load_latest_external_metrics()
    if not metrics:
        return ["- 外部KPIスナップショット未作成。次のself_improvement_loopで生成"]
    ga4 = metrics.get("traffic", {}).get("ga4", {})
    rev = metrics.get("revenue", {})
    intent = metrics.get("intent", {}).get("purchase_form", {})
    yt = metrics.get("youtube", {})
    site = metrics.get("site", {})
    health = metrics.get("health", {})
    items = [
        f"- updated: {metrics.get('ts', '--')}",
        f"- revenue: Polar orders={_value(rev.get('order_count'))}, gross={_value(rev.get('gross_jpy'))}円, source={'ok' if rev.get('available') else rev.get('unavailable_reason', 'unavailable')}",
        f"- GA4 today: PV={_value(ga4.get('pageviews_today'))}, /shop={_value(ga4.get('shop_pageviews_today'))}, /about={_value(ga4.get('about_pageviews_today'))}, source={'ok' if ga4.get('available') else ga4.get('unavailable_reason', 'unavailable')}",
        f"- intent form: total={_value(intent.get('total'))}, yes={_value(intent.get('yes'))}, maybe={_value(intent.get('maybe'))}, 24h={_value(intent.get('recent_24h'))}, source={'ok' if intent.get('available') else intent.get('unavailable_reason', 'unavailable')}",
        f"- YouTube: subscribers={_value(yt.get('subscriber_count'))}, views={_value(yt.get('view_count'))}, source={'ok' if yt.get('available') else yt.get('unavailable_reason', 'unavailable')}",
        f"- shop live: title={_value(site.get('shop_live', {}).get('title'))}, price={_value(site.get('shop_live', {}).get('price'))}",
        f"- shop local/live mismatch: {health.get('shop_local_live_mismatch', False)}",
    ]
    if health.get("unavailable"):
        names = ", ".join(f"{k}={v}" for k, v in list(health["unavailable"].items())[:3])
        items.append(f"- unavailable_sources: {names}")
    return items[:max_items]


def write_kpi_observations(metrics: dict[str, Any] | None = None) -> Path:
    metrics = metrics or load_latest_external_metrics()
    if not metrics:
        metrics = collect_external_metrics()
    ga4 = metrics.get("traffic", {}).get("ga4", {})
    rev = metrics.get("revenue", {})
    cog = metrics.get("cognition", {})
    intent = metrics.get("intent", {}).get("purchase_form", {})
    yt = metrics.get("youtube", {})
    site = metrics.get("site", {})
    health = metrics.get("health", {})

    def src(src_obj: dict[str, Any]) -> str:
        return "取得済み" if src_obj.get("available") else f"未取得: {src_obj.get('unavailable_reason', 'unknown')}"

    lines = [
        "# KPI 観察ログ（自動同期）",
        "",
        f"updated: {metrics.get('ts', now_jst_iso())}",
        "",
        "このファイルは `bot/external_metrics.py` が実測スナップショットから更新する。",
        "`0` は取得できたうえでゼロ、`未取得` はAPI/権限/実装未接続を意味する。",
        "",
        "## 収益・意向",
        "",
        "| 指標 | 値 | 状態 |",
        "|---|---:|---|",
        f"| Polar 注文数 | {_value(rev.get('order_count'))} | {src(rev)} |",
        f"| Polar 売上 | {_value(rev.get('gross_jpy'))}円 | {src(rev)} |",
        f"| 購入意思フォーム total | {_value(intent.get('total'))} | {src(intent)} |",
        f"| 購入意思フォーム yes | {_value(intent.get('yes'))} | {src(intent)} |",
        f"| 購入意思フォーム maybe | {_value(intent.get('maybe'))} | {src(intent)} |",
        f"| 購入意思フォーム 24h | {_value(intent.get('recent_24h'))} | {src(intent)} |",
        "",
        "## 流入・認知",
        "",
        "| 指標 | 値 | 状態 |",
        "|---|---:|---|",
        f"| GA4 PV today | {_value(ga4.get('pageviews_today'))} | {src(ga4)} |",
        f"| GA4 /shop PV today | {_value(ga4.get('shop_pageviews_today'))} | {src(ga4)} |",
        f"| GA4 /about PV today | {_value(ga4.get('about_pageviews_today'))} | {src(ga4)} |",
        f"| GitHub stars | {_value(cog.get('stars'))} | {src(cog)} |",
        f"| Zenn likes | {_value(cog.get('zenn_liked'))} | {src(cog)} |",
        f"| Hatena bookmarks | {_value(cog.get('hatena_bookmarks'))} | {src(cog)} |",
        f"| YouTube subscribers | {_value(yt.get('subscriber_count'))} | {src(yt)} |",
        f"| YouTube views | {_value(yt.get('view_count'))} | {src(yt)} |",
        "",
        "## 導線状態",
        "",
        "| 対象 | 値 |",
        "|---|---|",
        f"| live /shop title | {_value(site.get('shop_live', {}).get('title'))} |",
        f"| live /shop price | {_value(site.get('shop_live', {}).get('price'))} |",
        f"| live /shop intent CTA | {_value(site.get('shop_live', {}).get('has_intent_anchor'))} |",
        f"| local/live mismatch | {_value(health.get('shop_local_live_mismatch'))} |",
    ]
    if ga4.get("top_pages_today"):
        lines.extend(["", "## GA4 Top Pages Today", "", "| path | views |", "|---|---:|"])
        for page in ga4["top_pages_today"][:8]:
            lines.append(f"| {page.get('path', '')} | {_value(page.get('views'))} |")
    if health.get("unavailable"):
        lines.extend(["", "## 未取得ソース", ""])
        for name, reason in health["unavailable"].items():
            lines.append(f"- {name}: {reason}")
    KPI_OBSERVATIONS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return KPI_OBSERVATIONS_PATH


if __name__ == "__main__":
    result = collect_external_metrics()
    write_external_metrics_snapshot(result)
    write_kpi_observations(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
