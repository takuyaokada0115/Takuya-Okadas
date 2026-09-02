#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HPB 推奨クーポン自動生成ツール

対象店舗の「向こう2週間の空き時間枠」に対して、過去8〜9ヶ月の売上明細から
分析した売れ筋クーポンを、枠の空き時間に収まる施術時間で割り当てて推奨し、
HTML で一覧表示する。推奨クーポンは価格の昇順で並べる。

依存ライブラリなし（Python 標準ライブラリのみ）で動作する。

使い方:
    python3 recommend.py \
        --sales sample_sales.csv \
        --availability sample_availability.csv \
        --out ../../成果物/HPB推奨クーポン.html

入力データの形式は README.md を参照。
"""

from __future__ import annotations

import argparse
import csv
import html
import os
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta


# --------------------------------------------------------------------------
# 入力データの読み込み
# --------------------------------------------------------------------------
def load_sales(path: str) -> list[dict]:
    """売上明細 CSV を読み込む。

    想定列: 日付, クーポン名, 価格, 施術時間
        - 日付      : YYYY-MM-DD
        - クーポン名 : 文字列
        - 価格      : 円（整数）
        - 施術時間   : 分（整数）
    1 行 = 1 施術（1 会計）とみなす。
    """
    rows: list[dict] = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            name = (r.get("クーポン名") or "").strip()
            if not name:
                continue
            rows.append(
                {
                    "日付": (r.get("日付") or "").strip(),
                    "クーポン名": name,
                    "価格": _to_int(r.get("価格")),
                    "施術時間": _to_int(r.get("施術時間")),
                }
            )
    return rows


def load_availability(path: str) -> list[dict]:
    """空き枠 CSV を読み込む。

    想定列: 日付, 開始時刻, 空き時間
        - 日付     : YYYY-MM-DD
        - 開始時刻  : HH:MM
        - 空き時間  : 分（整数）。その枠に入れられる施術時間の上限。
    """
    slots: list[dict] = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            d = (r.get("日付") or "").strip()
            if not d:
                continue
            slots.append(
                {
                    "日付": d,
                    "開始時刻": (r.get("開始時刻") or "").strip(),
                    "空き時間": _to_int(r.get("空き時間")),
                }
            )
    return slots


def _to_int(value) -> int:
    """"6,600" や "90分" のような表記も整数化する。"""
    if value is None:
        return 0
    s = str(value).strip().replace(",", "")
    digits = "".join(ch for ch in s if ch.isdigit())
    return int(digits) if digits else 0


# --------------------------------------------------------------------------
# 売れ筋分析
# --------------------------------------------------------------------------
def aggregate_sales(rows: list[dict]) -> dict[str, dict]:
    """クーポン別に 件数 / 売上合計 / 代表価格 / 代表施術時間 を集計する。

    価格・施術時間はクーポンごとに最頻値（もっとも多く登場した値）を代表値とする。
    """
    counts: Counter = Counter()
    revenue: dict[str, int] = defaultdict(int)
    prices: dict[str, Counter] = defaultdict(Counter)
    minutes: dict[str, Counter] = defaultdict(Counter)

    for r in rows:
        name = r["クーポン名"]
        counts[name] += 1
        revenue[name] += r["価格"]
        if r["価格"]:
            prices[name][r["価格"]] += 1
        if r["施術時間"]:
            minutes[name][r["施術時間"]] += 1

    stats: dict[str, dict] = {}
    for name in counts:
        stats[name] = {
            "クーポン名": name,
            "件数": counts[name],
            "売上合計": revenue[name],
            "価格": prices[name].most_common(1)[0][0] if prices[name] else 0,
            "施術時間": minutes[name].most_common(1)[0][0] if minutes[name] else 0,
        }
    return stats


def top_sellers(stats: dict[str, dict], top: int) -> list[dict]:
    """売上合計の多い順に上位 top 件を返す（=売れ筋クーポン）。"""
    ordered = sorted(
        stats.values(), key=lambda s: (s["売上合計"], s["件数"]), reverse=True
    )
    return ordered[:top]


# --------------------------------------------------------------------------
# 空き枠 × 売れ筋クーポンのマッチング
# --------------------------------------------------------------------------
def filter_window(slots: list[dict], start: date, days: int) -> list[dict]:
    """start から days 日間（向こう2週間 = 14 日）の空き枠だけを残す。"""
    end = start + timedelta(days=days - 1)
    kept: list[dict] = []
    for s in slots:
        try:
            d = datetime.strptime(s["日付"], "%Y-%m-%d").date()
        except ValueError:
            continue
        if start <= d <= end:
            kept.append(s)
    kept.sort(key=lambda s: (s["日付"], s["開始時刻"]))
    return kept


def recommend_for_slots(
    slots: list[dict], sellers: list[dict], per_slot: int
) -> list[dict]:
    """各空き枠に、施術時間が枠に収まる売れ筋クーポンを割り当てる。

    推奨クーポンは価格の昇順で並べ、最大 per_slot 件まで表示する。
    """
    results: list[dict] = []
    for slot in slots:
        cap = slot["空き時間"]
        fit = [
            c for c in sellers if 0 < c["施術時間"] <= cap
        ]
        # 売れ筋順（売上合計）で候補を絞ってから、表示は価格の昇順に並べる。
        fit_by_sales = sorted(
            fit, key=lambda c: (c["売上合計"], c["件数"]), reverse=True
        )[:per_slot]
        recommended = sorted(fit_by_sales, key=lambda c: c["価格"])
        results.append({"slot": slot, "coupons": recommended})
    return results


# --------------------------------------------------------------------------
# HTML 出力
# --------------------------------------------------------------------------
def render_html(
    recommendations: list[dict],
    sellers: list[dict],
    period_start: date,
    period_days: int,
    generated_at: datetime,
) -> str:
    e = html.escape
    end = period_start + timedelta(days=period_days - 1)

    # 売れ筋クーポン（価格の昇順）
    sellers_by_price = sorted(sellers, key=lambda c: c["価格"])

    def yen(n: int) -> str:
        return f"¥{n:,}"

    # 日付ごとに空き枠をまとめる
    by_date: dict[str, list[dict]] = defaultdict(list)
    for rec in recommendations:
        by_date[rec["slot"]["日付"]].append(rec)

    parts: list[str] = []
    parts.append(
        """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HPB 推奨クーポン</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, "Hiragino Kaku Gothic ProN", "Yu Gothic",
         Meiryo, sans-serif; margin: 0; padding: 24px; line-height: 1.6;
         background: #fafafa; color: #1a1a1a; }
  @media (prefers-color-scheme: dark) {
    body { background: #1a1a1a; color: #eaeaea; }
    .card, .day { background: #242424; border-color: #383838; }
    th { background: #2e2e2e; }
    tr:nth-child(even) td { background: #202020; }
  }
  h1 { font-size: 1.5rem; margin: 0 0 4px; }
  .meta { color: #888; font-size: .85rem; margin-bottom: 24px; }
  h2 { font-size: 1.15rem; margin: 28px 0 12px; border-left: 4px solid #e8638a;
       padding-left: 10px; }
  table { border-collapse: collapse; width: 100%; margin: 8px 0 20px;
          font-size: .9rem; }
  th, td { border: 1px solid #ddd; padding: 8px 10px; text-align: left; }
  th { background: #f0f0f0; }
  tr:nth-child(even) td { background: #f7f7f7; }
  .num { text-align: right; white-space: nowrap; }
  .day { border: 1px solid #e5e5e5; border-radius: 10px; padding: 14px 16px;
         margin-bottom: 14px; background: #fff; }
  .day h3 { margin: 0 0 10px; font-size: 1rem; }
  .slot { margin: 10px 0; padding: 10px 12px; border: 1px solid #eee;
          border-radius: 8px; }
  .slot-head { font-weight: 600; margin-bottom: 6px; }
  .empty { color: #b00; font-size: .85rem; }
  .badge { display: inline-block; background: #e8638a; color: #fff;
           border-radius: 999px; padding: 1px 8px; font-size: .75rem;
           margin-left: 6px; }
  .card { border: 1px solid #e5e5e5; border-radius: 10px; padding: 16px;
          background: #fff; margin-bottom: 24px; }
</style>
</head>
<body>
"""
    )
    parts.append(f"<h1>HPB 推奨クーポン</h1>")
    parts.append(
        f'<div class="meta">対象期間: {period_start:%Y-%m-%d}（{end:%Y-%m-%d} まで '
        f"{period_days} 日間） / 生成日時: {generated_at:%Y-%m-%d %H:%M}</div>"
    )

    # 売れ筋ランキング（価格の昇順）
    parts.append('<div class="card">')
    parts.append("<h2>売れ筋クーポン（価格の昇順）</h2>")
    parts.append("<table>")
    parts.append(
        "<tr><th>クーポン名</th><th class='num'>価格</th>"
        "<th class='num'>施術時間</th><th class='num'>販売件数</th>"
        "<th class='num'>売上合計</th></tr>"
    )
    for c in sellers_by_price:
        parts.append(
            f"<tr><td>{e(c['クーポン名'])}</td>"
            f"<td class='num'>{yen(c['価格'])}</td>"
            f"<td class='num'>{c['施術時間']}分</td>"
            f"<td class='num'>{c['件数']}件</td>"
            f"<td class='num'>{yen(c['売上合計'])}</td></tr>"
        )
    parts.append("</table>")
    parts.append("</div>")

    # 空き枠ごとの推奨
    parts.append("<h2>空き枠ごとの推奨クーポン</h2>")
    if not recommendations:
        parts.append(
            '<p class="empty">対象期間内に空き枠が見つかりませんでした。</p>'
        )
    for d in sorted(by_date):
        try:
            dobj = datetime.strptime(d, "%Y-%m-%d").date()
            wd = "月火水木金土日"[dobj.weekday()]
            label = f"{dobj:%Y-%m-%d}（{wd}）"
        except ValueError:
            label = d
        parts.append('<div class="day">')
        parts.append(f"<h3>{e(label)}</h3>")
        for rec in by_date[d]:
            slot = rec["slot"]
            parts.append('<div class="slot">')
            parts.append(
                f'<div class="slot-head">{e(slot["開始時刻"])}〜 '
                f'空き {slot["空き時間"]}分</div>'
            )
            if not rec["coupons"]:
                parts.append(
                    '<div class="empty">この枠に収まる売れ筋クーポンなし</div>'
                )
            else:
                parts.append("<table>")
                parts.append(
                    "<tr><th>推奨クーポン（価格昇順）</th>"
                    "<th class='num'>価格</th><th class='num'>施術時間</th></tr>"
                )
                for c in rec["coupons"]:
                    parts.append(
                        f"<tr><td>{e(c['クーポン名'])}</td>"
                        f"<td class='num'>{yen(c['価格'])}</td>"
                        f"<td class='num'>{c['施術時間']}分</td></tr>"
                    )
                parts.append("</table>")
            parts.append("</div>")
        parts.append("</div>")

    parts.append("</body></html>")
    return "\n".join(parts)


# --------------------------------------------------------------------------
# エントリポイント
# --------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(
        description="HPB 空き枠に売れ筋クーポンを推奨し HTML 出力する"
    )
    p.add_argument(
        "--sales",
        default=os.path.join(here, "sample_sales.csv"),
        help="売上明細 CSV のパス",
    )
    p.add_argument(
        "--availability",
        default=os.path.join(here, "sample_availability.csv"),
        help="空き枠 CSV のパス",
    )
    p.add_argument(
        "--out",
        default=os.path.join(here, "..", "..", "成果物", "HPB推奨クーポン.html"),
        help="出力する HTML のパス",
    )
    p.add_argument(
        "--from",
        dest="from_date",
        default=None,
        help="対象開始日 YYYY-MM-DD（既定: 今日）",
    )
    p.add_argument("--days", type=int, default=14, help="対象日数（既定: 14 = 2週間）")
    p.add_argument(
        "--top", type=int, default=8, help="売れ筋として扱う上位件数（既定: 8）"
    )
    p.add_argument(
        "--per-slot",
        type=int,
        default=3,
        help="1 枠あたりの推奨クーポン数（既定: 3）",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    start = (
        datetime.strptime(args.from_date, "%Y-%m-%d").date()
        if args.from_date
        else date.today()
    )

    sales_rows = load_sales(args.sales)
    stats = aggregate_sales(sales_rows)
    sellers = top_sellers(stats, args.top)

    all_slots = load_availability(args.availability)
    slots = filter_window(all_slots, start, args.days)

    recommendations = recommend_for_slots(slots, sellers, args.per_slot)

    out_html = render_html(
        recommendations, sellers, start, args.days, datetime.now()
    )

    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out_html)

    print(f"売上明細: {len(sales_rows)} 行 / クーポン {len(stats)} 種")
    print(f"売れ筋 上位: {len(sellers)} 種")
    print(f"対象空き枠: {len(slots)} 枠（{start} から {args.days} 日間）")
    print(f"HTML を書き出しました: {out_path}")


if __name__ == "__main__":
    main()
