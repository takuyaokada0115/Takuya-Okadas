"""下北沢店 2026年7月 売上実績（8月支給・7月分売上）。

出典: HPBサロンボード「スタッフ別 売上情報」＋「店販月別集計」（スタッフ別内訳）。
※ 割引／キャンセル料は反映されない集計値。
※ 店販列 = 物販商品(product) + 回数券(coupon) + 指名料(nomination) に分解済み。

各値の検算（施術+オプション+店販=総売上）は test 相当でモジュール読込時に assert。
"""

from models import Performance

STORE = "下北沢店"
YEAR_MONTH = "2026-07"

# HPB表示名 → (staff_id or None, Performance)
PERF: dict[str, tuple] = {
    # Masumi = 谷本 真澄（S001・店長）
    "Masumi": ("S001", Performance(
        tech_sales=609_580, option_sales=51_600,
        product_sales=27_000,   # 美容液22,600 + HBL beauty4,400
        coupon_sales=34_200,    # 回数券
        nomination_fee=31_200,  # 指名料
        tech_count=139, nomination_count=6,
    )),
    # Matsufuji = 未登録（雇用契約書 未提供）
    "Matsufuji": (None, Performance(
        tech_sales=377_280, option_sales=19_100,
        product_sales=15_400,   # 美容液15,400
        coupon_sales=0,
        nomination_fee=2_500,   # 指名料
        tech_count=72, nomination_count=5,
    )),
    # Itou = 伊東 真菜（S002）
    "Itou": ("S002", Performance(
        tech_sales=577_000, option_sales=47_500,
        product_sales=15_400,   # 美容液15,400
        coupon_sales=53_400,    # 回数券
        nomination_fee=6_600,   # 指名料
        tech_count=133, nomination_count=2,
    )),
    # Y.Reina = 横井 零奈（S004）
    "Y.Reina": ("S004", Performance(
        tech_sales=164_700, option_sales=6_000,
        product_sales=4_400,    # 美容液4,400
        coupon_sales=0,
        nomination_fee=0,
        tech_count=33, nomination_count=0,
    )),
}

# HPB「スタッフ別売上情報」の各列（検算用の正解値）
_EXPECTED = {
    "Masumi":    dict(retail=92_400, total=753_580),
    "Matsufuji": dict(retail=17_900, total=414_280),
    "Itou":      dict(retail=75_400, total=699_900),
    "Y.Reina":   dict(retail=4_400,  total=175_100),
}

# 読込時に検算（HPBの店販列・総売上列と一致することを保証）
for _name, (_sid, _p) in PERF.items():
    assert _p.retail_total == _EXPECTED[_name]["retail"], f"{_name} 店販不一致"
    assert _p.total_sales == _EXPECTED[_name]["total"], f"{_name} 総売上不一致"
