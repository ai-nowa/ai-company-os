"""Lemon Squeezy 商品・バリアント確認 + Checkout URL生成スクリプト。
NOTE: 商品(Product)・バリアント(Variant)はAPIで作成不可（ダッシュボードのみ）。
      https://app.lemonsqueezy.com でいくとが先に作成してから実行してください。

実行: bot/.venv/bin/python -m bot.ls_setup_product
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from bot.lemonsqueezy_client import (
    list_products,
    list_variants,
    create_checkout,
)


def main() -> None:
    products = list_products()
    if not products:
        print("[ERROR] 商品が見つかりません。")
        print("手順: https://app.lemonsqueezy.com → Products → New Product")
        print("  - 商品名: AIチーム設計キット v0.1")
        print("  - バリアント価格: 7800 JPY")
        print("  - テストモード: ON")
        sys.exit(1)

    print(f"[OK] {len(products)}件の商品を取得")
    for p in products:
        pid = p["id"]
        name = p["attributes"]["name"]
        slug = p["attributes"]["slug"]
        print(f"  Product id={pid} name={name} slug={slug}")

        variants = list_variants(pid)
        for v in variants:
            vid = v["id"]
            vname = v["attributes"]["name"]
            price = v["attributes"]["price"]
            test = v["attributes"].get("test_mode", False)
            print(f"    Variant id={vid} name={vname} price={price} test_mode={test}")

            print(f"    Checkout URL を生成中...")
            url = create_checkout(vid, test_mode=test)
            print(f"    [OK] Checkout URL: {url}")
            print()
            print("=== shop/index.html に設定する値 ===")
            print(f"VARIANT_ID: {vid}")
            print(f"CHECKOUT_URL: {url}")


if __name__ == "__main__":
    main()
