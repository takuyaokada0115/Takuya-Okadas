"""下北沢店 2026年8月 売上実績（9月支給）。町田分は次スレッドで合算。

出典: HPBサロンボード「スタッフ別売上情報」＋「店販月別集計」。
店販列 = 物販(product) + 回数券(coupon) + 指名料(nomination) に分解。
"""

from models import Performance

STORE = "下北沢店"
YEAR_MONTH = "2026-08"

PERF: dict[str, tuple] = {
    "Masumi": ("S001", Performance(
        tech_sales=662_460, option_sales=55_950,
        product_sales=35_570, coupon_sales=63_900, nomination_fee=33_600,
        tech_count=141, nomination_count=10,
    )),
    "Matsufuji": (None, Performance(   # 業務委託(別体系)
        tech_sales=506_160, option_sales=22_100,
        product_sales=4_400, coupon_sales=0, nomination_fee=5_000,
        tech_count=105, nomination_count=4,
    )),
    "Itou": ("S002", Performance(
        tech_sales=622_560, option_sales=49_950,
        product_sales=45_000, coupon_sales=44_700, nomination_fee=11_400,
        tech_count=137, nomination_count=7,
    )),
    "Y.Reina": ("S004", Performance(   # 下北沢分のみ（町田分は次スレッドで合算）
        tech_sales=149_200, option_sales=5_600,
        product_sales=4_400, coupon_sales=0, nomination_fee=300,
        tech_count=27, nomination_count=0,
    )),
}

# 検算（店販列・総売上がHPB表示と一致）
_CHECK = {
    "Masumi":    (133_070, 851_480),
    "Matsufuji": (9_400,   537_660),
    "Itou":      (101_100, 773_610),
    "Y.Reina":   (4_700,   159_500),
}
for _n, (_sid, _p) in PERF.items():
    assert _p.retail_total == _CHECK[_n][0], f"{_n} 店販不一致 {_p.retail_total}"
    assert _p.total_sales == _CHECK[_n][1], f"{_n} 総売上不一致 {_p.total_sales}"
