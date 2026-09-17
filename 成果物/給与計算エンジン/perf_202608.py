"""2026年8月分 全社員 実績＋勤怠（9月支給）。下北沢＋町田。横井は両店合算。

売上: HPBサロンボード（下北沢・町田のスタッフ別売上情報＋店販月別集計）。
勤怠: LINEタイムカード2026-08（実労働=退勤-出勤-休憩1h）。overtime_hours=実働-所定8hの月合計。
      みなし枠25h・実残業は全員25h未満→追加残業ゼロ。
"""

from models import Attendance, Performance

YEAR_MONTH = "2026-08"

# staff_id -> (Performance, Attendance, is_training)
DATA: dict[str, tuple] = {
    "S001": (Performance(  # 谷本(下北沢・店長)
        tech_sales=662_460, option_sales=55_950,
        product_sales=35_570, coupon_sales=63_900, nomination_fee=33_600,
        tech_count=141, nomination_count=10,
    ), Attendance(overtime_hours=1412/60), False),  # 実働-8h=23h32m
    "S002": (Performance(  # 伊東(下北沢)
        tech_sales=622_560, option_sales=49_950,
        product_sales=45_000, coupon_sales=44_700, nomination_fee=11_400,
        tech_count=137, nomination_count=7,
    ), Attendance(overtime_hours=440/60), False),   # 7h20m
    "S003": (Performance(  # 山口(町田) ※キャンペーン3,600はcoupon扱い(物販5%対象外)
        tech_sales=648_160, option_sales=26_200,
        product_sales=0, coupon_sales=3_600, nomination_fee=3_600,
        tech_count=125, nomination_count=10,
    ), Attendance(overtime_hours=990/60), False),   # 16h30m
    "S004": (Performance(  # 横井(下北沢+町田 合算)
        tech_sales=149_200 + 512_260, option_sales=5_600 + 15_200,
        product_sales=4_400 + 6_200, coupon_sales=0,
        nomination_fee=300 + 5_400,
        tech_count=27 + 94, nomination_count=0 + 3,
    ), Attendance(overtime_hours=871/60), False),   # 14h31m
}

_CHECK = {  # (店販列合計, 総売上)
    "S001": (133_070, 851_480),
    "S002": (101_100, 773_610),
    "S003": (7_200, 681_560),
    "S004": (4_700 + 11_600, 159_500 + 539_060),
}
for _sid, (_p, _a, _t) in DATA.items():
    assert _p.retail_total == _CHECK[_sid][0], f"{_sid} 店販不一致 {_p.retail_total}"
    assert _p.total_sales == _CHECK[_sid][1], f"{_sid} 総売上不一致 {_p.total_sales}"
