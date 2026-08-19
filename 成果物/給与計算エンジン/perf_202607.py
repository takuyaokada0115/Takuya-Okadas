"""2026年7月分 全スタッフ実績＋勤怠（8月支給）。下北沢店＋町田店。

売上出典: HPBサロンボード（スタッフ別売上情報＋店販月別集計）。
名寄せ:
  Masumi=谷本真澄(S001/下北沢/店長), Itou=伊東真菜(S002/下北沢/まな),
  Y.Suzuka=山口涼風(S003/町田/涼風),
  横井零奈(S004)= 下北沢「Y.Reina」+ 町田「Reina」を合算（両店勤務・★要確認）。
  Matsufuji=未登録（雇用契約書未提供）。

勤怠出典: LINEタイムカード（2026-07）。残業=各日19:00以降の退社分を月合計（訂正メッセージ反映）。
  overtime_hours は月合計（エンジンが固定残業時間を差し引いて追加分を算出）。
"""

from models import Attendance, Performance

STORE = "下北沢店＋町田店"
YEAR_MONTH = "2026-07"

# staff_id -> (Performance, Attendance月合計残業h, is_training)
DATA: dict[str, tuple] = {
    # 谷本 真澄（下北沢・店長）
    "S001": (Performance(
        tech_sales=609_580, option_sales=51_600,
        product_sales=27_000, coupon_sales=34_200, nomination_fee=31_200,
        tech_count=139, nomination_count=6,
    ), Attendance(overtime_hours=972/60, holiday_hours=4.0), False),  # 7/21 半日休日出勤(採用面接)=4h暫定
    # 伊東 真菜（下北沢・まな）
    "S002": (Performance(
        tech_sales=577_000, option_sales=47_500,
        product_sales=15_400, coupon_sales=53_400, nomination_fee=6_600,
        tech_count=133, nomination_count=2,
    ), Attendance(overtime_hours=177/60), False),
    # 山口 涼風（町田・Y.Suzuka）※キャンペーン5,400はcoupon扱い(物販5%対象外・暫定)
    "S003": (Performance(
        tech_sales=748_680, option_sales=35_400,
        product_sales=24_200, coupon_sales=5_400, nomination_fee=2_400,
        tech_count=147, nomination_count=6,
    ), Attendance(overtime_hours=550/60), False),
    # 横井 零奈（下北沢 Y.Reina + 町田 Reina を合算）
    "S004": (Performance(
        tech_sales=164_700 + 491_720, option_sales=6_000 + 11_900,
        product_sales=4_400 + 12_800, coupon_sales=0,
        nomination_fee=0 + 5_700,
        tech_count=33 + 97, nomination_count=0 + 3,
    ), Attendance(overtime_hours=702/60), False),
}

# 検算: 各人の店販列・総売上（下北沢/町田のHPB表示値と一致）
_CHECK = {
    "S001": (92_400, 753_580),
    "S002": (75_400, 699_900),
    "S003": (32_000, 816_080),
    "S004": (4_400 + 18_500, 175_100 + 522_120),  # 横井合算
}
for _sid, (_p, _a, _t) in DATA.items():
    assert _p.retail_total == _CHECK[_sid][0], f"{_sid} 店販不一致 {_p.retail_total}"
    assert _p.total_sales == _CHECK[_sid][1], f"{_sid} 総売上不一致 {_p.total_sales}"

# マスタ未登録（雇用条件未提供）: Matsufuji（下北沢）
MATSUFUJI = Performance(
    tech_sales=377_280, option_sales=19_100,
    product_sales=15_400, coupon_sales=0, nomination_fee=2_500,
)
