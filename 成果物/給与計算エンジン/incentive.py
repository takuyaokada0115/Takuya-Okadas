"""売上インセンティブ・各種コミッションの計算。

出典: 新インセンティブ表（2026-07-18 受領）
- 売上インセンティブは％では表現できない段差（¥950,000の行）があるため、
  表の値をそのまま使うルックアップ方式で実装する。
- 判定基準は「総売上」= 技術売上 + 物販 + オプション + 指名料（確定事項）。
"""

# 売上（下限しきい値）→ バック単価（固定額）
INCENTIVE_TABLE = [
    (650_000, 6_500),
    (700_000, 14_000),
    (750_000, 22_500),
    (800_000, 32_000),
    (850_000, 42_500),
    (900_000, 54_000),
    (950_000, 76_000),
    (1_000_000, 90_000),
]

# ¥1,100,000 以上は「売上 × 10%」（定額でなく率）
INCENTIVE_RATE_THRESHOLD = 1_100_000
INCENTIVE_RATE = 0.10

# 各種コミッション率
RETAIL_RATE = 0.05       # 物販（店販）
OPTION_RATE = 0.05       # オプション
NOMINATION_RATE = 1.00   # 指名料（全額を本人へ）


def sales_incentive(total_sales: int) -> int:
    """総売上から売上インセンティブ（バック単価）を求める。

    - ¥650,000 未満は ¥0
    - ¥1,100,000 以上は 総売上 × 10%
    - それ以外は、しきい値以上・次のしきい値未満の行の固定額
    """
    if total_sales >= INCENTIVE_RATE_THRESHOLD:
        return int(total_sales * INCENTIVE_RATE)

    amount = 0
    for threshold, back in INCENTIVE_TABLE:
        if total_sales >= threshold:
            amount = back
        else:
            break
    return amount


def retail_commission(retail_sales: int) -> int:
    """物販（店販）コミッション = 物販売上 × 5%。"""
    return round(retail_sales * RETAIL_RATE)


def option_commission(option_sales: int) -> int:
    """オプション販売コミッション = オプション売上 × 5%。"""
    return round(option_sales * OPTION_RATE)


def nomination_pay(nomination_fee: int) -> int:
    """指名料 = 指名料売上 × 100%（全額）。"""
    return round(nomination_fee * NOMINATION_RATE)
